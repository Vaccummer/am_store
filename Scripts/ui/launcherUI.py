import os
import sys
from Scripts.tools.toolbox import *
from Scripts.manager.paths_transfer import *
from PySide2.QtWidgets import QListWidget, QMainWindow, QWidget,QListWidgetItem,QPushButton, QHBoxLayout, QVBoxLayout, QLabel
from PySide2.QtGui import QFontMetrics, QIcon
from PySide2.QtCore import QSize, Qt
from Scripts.ui.custom_widget import *
from functools import partial
import shutil
import pandas
import pathlib
import aiofiles
import asyncio
import asyncssh
from typing import List, Literal, Union, OrderedDict

class Associate:
    def __init__(self, nums:int, 
                 program_info_df:dict[str, pandas.DataFrame],
                 path_manager:PathManager,):
        self.num = nums
        self.df = program_info_df
        self._load()
        self.pathid:PathManager = path_manager
    
    def _load(self):
        self.names = []
        self.ch_names = []
        self.exe_path = []
        self.groups = []
        for group, df_i in self.df.items():
            self.names.extend(df_i['Name'].to_list())
            self.ch_names.extend(df_i['Chinese Name'].to_list())
            self.exe_path.extend(df_i['EXE Path'].to_list())
            self.groups.extend([group]*len(df_i))
    
    # To Associate subdirectory of certain path
    def ass_path(self, prompt_f):
        if not prompt_f:
            return [], []
        prompt_f_s = self.pathid.check(prompt_f,)
        if prompt_f_s is None:
            pass
        elif stat.S_ISDIR(prompt_f_s.st_mode):
            return self.pathid.listdir(prompt_f)
        else:
            return [], []
        dir_n, base_n = os.path.split(prompt_f)
        dir_n_s = self.pathid.check(dir_n)
        if dir_n_s is None:
            return [], []
        if stat.S_ISDIR(dir_n_s.st_mode):
            names_l, stat_l = self.pathid.listdir(dir_n)
        else:
            return [], []
        names_l_t = []
        for name_i, stat_i in zip(names_l, stat_l):
            if base_n.lower() in name_i.lower():
                base_index = (name_i.lower()).index(base_n.lower())
                names_l_t.append((name_i, stat_i, base_index))
        names_l_1 = sorted(names_l_t, key=lambda x: x[2])
        names_t = [i[0] for i in names_l_1]
        type_t = [i[1] for i in names_l_1]
        return names_t, type_t

    # To associate a programme name of prompt
    def ass_name(self, prompt_f)->Tuple[List[str], List[Literal['app']]]:
        if not prompt_f:
            return [], []
        output_name = sorted([name_i for name_i in self.names if prompt_f.lower() in name_i.lower()], key=lambda s: (s.lower().index(prompt_f.lower()))/len(s))
        output_chname = sorted([ch_name_i for ch_name_i in self.ch_names if prompt_f.lower() in ch_name_i.lower()], key=lambda s: (s.lower().index(prompt_f.lower()))/len(s))
        output_chname_t = [i for i in output_chname if self.names[self.ch_names.index(i)] not in output_name]
        names_t = rm_dp_list_elem(output_name+output_chname_t, reverse=False)[0:self.num]
        return names_t, ['app']*len(names_t)
    
    # To associate programmes with multiple prompts
    def multi_pro_name(self, prompt_list_f):
        output_0 = list_overlap([self.name(prompt_if)[0] for prompt_if in prompt_list_f])
        output_1 = [self.names[(self.ch_names).index(ch_name_i)] for ch_name_i in list_overlap([self.name(prompt_if)[1] for prompt_if in prompt_list_f])]
        out_t = (output_0+output_1)[0:self.num]
        return out_t, ['app']*len(out_t)
    
    def ass_get(self, prompt:str):
        if is_path(prompt):
            return self.ass_path(prompt)
        else:
            if ";" in prompt:
                return self.multi_pro_name(prompt.split(';'))
            return self.ass_name(prompt)
    
    def fill(self, prompt:str)->Tuple[List[str], List[os.stat_result]]:
        if is_path(prompt):
            return self.fill_path(prompt)
        else:
            return self.fill_name(prompt)
        
    # Automatically complete PATH
    def fill_path(self, prompt_f:str)->Union[None, str]:
        # if prompt is a exsisting path
        name_l, stat_l = self.ass_path(prompt_f)
        if not name_l:
            return None
        path_check = self.pathid.check(prompt_f)
        if path_check is None:
            pass
        elif stat.S_ISDIR(path_check.st_mode):
            if len(name_l) == 1:
                return os.path.join(prompt_f, name_l[0])
        else:
            return None
        dir_ni, base_ni = os.path.split(prompt_f)
        wait_l0 = [name_i for name_i in name_l if name_i.startswith(base_ni)]
        wait_l1 = [name_i for name_i in name_l if name_i.lower().startswith(base_ni.lower())]
        if len(wait_l0) == 1:
            return os.path.join(dir_ni, wait_l0[0])
        elif len(wait_l0+wait_l1) == 1:
            return os.path.join(dir_ni, wait_l1[0])
    
    # Automatically complete Name
    def fill_name(self, prompt_f:str) -> Union[None, str]:
        output_0 = [name_i for name_i in self.names if name_i.startswith(prompt_f)]
        output_1 = [name_i for name_i in self.names if name_i.lower().startswith(prompt_f.lower())]
        output_2 = [ch_name_i for ch_name_i in self.ch_names if ch_name_i.startswith(prompt_f)]
        if len(output_0) == 1:
            return output_0[0]
        elif len(output_1+output_1) == 1:
            return output_1[0]
        elif len(output_2) == 1:
            return self.names[self.ch_names.index(output_2[0])]

class BasicAS(QListWidget, QObject):
    def __init__(self, config:Config_Manager, parent:Union[QMainWindow, QWidget],manager:LauncherPathManager):
        super().__init__(parent)
        self.up = parent
        self.name = "associate_list"
        self.config = config.deepcopy()
        self.setAcceptDrops(True)  # 接受放置事件
        self.setDragEnabled(True)  # 启用拖动事件
        self.config.group_chose("Launcher", self.name)
        self.launcher_manager = manager
        self._loadconfig(self.config)
        # UIUpdater.set(self.config, self._loadconfig, type_f='config')
        self._load()
        
    def focusNextPrevChild(self, next):
        return True
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():  # 检查是否有文件 URL
            event.acceptProposedAction()  # 接受拖入
        else:
            super().dragEnterEvent(event)
    def dragMoveEvent(self, event: QDragMoveEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)
    def dropEvent(self, event: QDropEvent):
        mime_data = event.mimeData()
        if mime_data.hasUrls():  # 如果拖放的内容是文件
            urls = mime_data.urls()
            paths = [url.toLocalFile() for url in urls]  # 获取文件路径
            self._upload(paths)
            event.acceptProposedAction()  # 接受拖放
        else:
            super().dropEvent(event)
    
    @abstractmethod
    def _upload(self, src:str):
        pass
    
    def _loadconfig(self, config:Config_Manager):
        # dynamic load
        pre = ['Launcher', self.name]
        self.num = config[atuple(pre+['max_exe_num'])]
        self.max_num = config[atuple(pre+['max_dir_num'])]
        self.max_length = config[atuple(pre+['max_length'])]

        pre = ['Launcher', self.name, 'path']
        self.download_dir = config[atuple(pre+['download_save_dir'])]
        self.filelog_default_path = config[atuple(pre+['filelog_default_path'])]
        self.exe_icon_getter = config[atuple(pre+['exe_icon_getter'])]
        self.file_icon_getter = config[atuple(pre+['file_icon_getter'])]
        
    def _load(self):
        # static load
        self.pre = atuple('Launcher', self.name)
        self.button_config = atuple('Launcher', self.name,'style','button')
        self.label_config = atuple('Launcher', self.name, 'style', 'label')
        self.main_config = atuple('Launcher', self.name, 'style', 'main')
        self.item_config = atuple('Launcher', self.name, 'style', 'item')
        self.scroll_bar_config = atuple('Launcher', self.name, 'style', 'scroll_bar')
        self.font_a = atuple('Launcher', self.name, 'font', 'main')

        # size
        pre = ['Launcher', self.name, 'Size']
        self.item_height = atuple(pre+['item_height'])
        self.button_height = atuple(pre+['button_height'])
        self.extra_width = atuple(pre+['extra_width'])
        self.max_width = atuple(pre+['max_width'])
        self.min_width = atuple(pre+['min_width'])

        self.launcher_df = self.launcher_manager.df
        self.path_manager:PathManager = self.up.path_manager
        self.ass = Associate(self.max_num, self.launcher_df, self.path_manager)
        self.config.group_chose(mode="Launcher", widget=self.name, obj=None)

        self._load_default_icons()

    def _load_default_icons(self) -> dict:
        self.file_icon_folder = self.config.get('file_icon_folder', mode="Launcher", widget=self.name, obj="path")
        
        self.file_icon_d = {}
        for name_i in os.listdir(self.file_icon_folder):
            name, ext = os.path.splitext(name_i)
            self.file_icon_d[name] = QIcon(os.path.join(self.file_icon_folder, name_i))
        
        pre = ["Launcher", self.name, "path"]
        default_folder_icon = atuple(pre+['default_folder_icon'])
        default_file_icon = atuple(pre+['default_file_icon'])
        default_back_icon = atuple(pre+['default_back_icon'])
        self.default_icon_d = {'dir':default_folder_icon, 'file':default_file_icon, 'back':default_back_icon}

    def cal_chunck_size(self, size_f:int, hosttype:Literal['local', 'remote'])->int:
        if hosttype == 'local':
            return min(max(self.local_min_chunck, size_f//48), self.local_max_chunck)
        else:
            return min(max(self.remote_min_chunck, size_f//48), self.remote_max_chunck)
    
    def _geticon(self, name:str, sign:Literal['name', "path"], stat_f:os.stat_result)->QIcon:
        match sign:
            case "name":
                return self.launcher_manager.get_icon(name)
            case _:
                if isinstance(stat_f, str) and stat_f == 'back':
                    return self.default_icon_d.get('back', self.default_icon_d.get('dir',''))
                elif stat.S_ISDIR(stat_f.st_mode):
                    return self.default_icon_d['dir']
                else:
                    for key, value in self.file_icon_d.items():
                        if name.endswith(f'.{key}'):
                            return value
                    return self.default_icon_d['file']
                  
    def _changeicon(self, index_i):
        app_name = self.label_l[index_i].text
        options = QFileDialog.Options()
        file_filter = "SVG Files (*.svg);;ICO Files (*.ico);;PNG Files (*.png)"
        file_path, _ = QFileDialog.getOpenFileName(self, f"Choose '{app_name}' icon", "", file_filter, options=options)

        if not file_path:
            return
        file_type = os.path.splitext(file_path)[-1]
        dst = os.path.join(os.path.basename(self.ass_icon_list[0]), app_name+file_type)
        path = glob(os.path.join(os.path.basename(self.ass_icon_list[0]), app_name+".*"))
        for path_i in path:
            os.remove(path_i)
        shutil.copy2(file_path, dst)
        self.button_l[index_i].setIcon(QIcon(dst))
    
    def _get_prompt(self)->str:
        return self.up.input_box.text()
class UIAS(BasicAS):
    def __init__(self, config:Config_Manager, parent:Union[QMainWindow, QWidget],manager:LauncherPathManager):  
        super().__init__(config, parent, manager)
        UIUpdater.set(self.font_a, self.setFont, 'font')
        UIUpdater.set(alist(self.main_config, self.item_config, self.scroll_bar_config), self.customStyle)
        self._inititems()
        self.setFocusPolicy(Qt.NoFocus)

    def customStyle(self, main_config:dict, item_config:dict, bar_config:dict):
        # dynamic style set
        main_bg = main_config.get('background', 'transparent')
        main_border = main_config.get('border', 'none')
        main_radius = main_config.get('border_radius', 20)


        item_bg_colors = enlarge_list(item_config.get('background_colors', ['#F7F7F7']),3)
        item_border = item_config.get('border', 'none')
        item_border_radius = item_config.get('border_radius', 10)
        item_padding = item_config.get('padding', [10,5,5,5])
        height_f = item_config.get('height', 50)

        bar_handle_colors = enlarge_list(bar_config.get('background_colors', ['#32CC99']),3)
        orbit_color = bar_config.get('orbit_color', '#F7F7F7')
        bar_radius = bar_config.get('border_radius', 7)
        bar_width = bar_config.get('width', 15)
        bar_height = bar_config.get('height', 30)

        self.style_d = {
            'QListWidget': {
                'border': main_border,
            },
            'QListView': {
                'background': main_bg,
                'border': main_border,
                'border-radius': main_radius,
            },
            'QListView::item': {
                'border': item_border,
                "padding": f"{item_padding[2]}px {item_padding[1]}px {item_padding[3]}px {item_padding[0]}px",
                'background-color': item_bg_colors[0],
                'border-radius': f"{item_border_radius}px",
                'height': f"{height_f}px",
            },
            'QListView::item:hover': {
                'background-color': item_bg_colors[1],
            },
            'QListView::item:selected': {
                'background-color': item_bg_colors[2],
            },
            'QListWidget QScrollBar:vertical': {
                'background': orbit_color,
                'width': f"{bar_width}px",
                'margin': '3px',
                'border-radius': f"{bar_radius}px",
            },
            'QListWidget QScrollBar::handle': {
                'background': bar_handle_colors[0],
                'min-height': f"{bar_height}px",
                'border-radius': f"{bar_radius}px",
            },
            'QListWidget QScrollBar::handle::hover': {
                'background': bar_handle_colors[1],
            },
            'QListWidget QScrollBar::handle::selected': {
                'background': bar_handle_colors[2],
            },
            "QListWidget QScrollBar::add-line,QListWidget QScrollBar::sub-line":{
                'background': 'none',
                'height': '0px',
            },
            "QListWidget QScrollBar::add-page,QListWidget QScrollBar::sub-page":{
                'background': 'none',

            }
        }
        self.style_sheet = style_make(self.style_d)
        self.setStyleSheet(self.style_sheet)
        self.setSpacing(1)  # 设置 item 之间的间距为 10 像素
        self.setAttribute(Qt.WA_TranslucentBackground) 

    def _init_signle_item(self, button_size:atuple, index_f:int, label_font:atuple=None):
        label_font = self.font_a if label_font is None else label_font
        item_i = QListWidgetItem()
        item_i.setData(Qt.UserRole, int(index_f))
        button_i = YohoPushButton(icon_i=self.default_icon_d['dir'], style_config=self.button_config, size_f=button_size)
        label_i = AutoLabel(text="Default", font=label_font, style_config=self.label_config)
        label_i.setAlignment(Qt.AlignLeft)
        UIUpdater.set(button_size, label_i.setFixedHeight)
        layout_i = amlayoutH(align_v='l')
        layout_i.setContentsMargins(0,0,0,0)
        layout_i.addWidget(button_i)
        layout_i.addWidget(label_i)
        widget_i = QWidget()
        widget_i.setLayout(layout_i)
        self.addItem(item_i)
        self.setItemWidget(item_i, widget_i)
        return item_i, button_i, label_i

    def _inititems(self):
        self.button_l = []
        self.label_l = []
        self.item_l = []
        for i in range(self.max_num):
            item_i, button_i, label_i = self._init_signle_item(self.button_height, i)
            item_i.setHidden(True)
            self.item_l.append(item_i)
            self.button_l.append(button_i)
            self.label_l.append(label_i)
            button_i.clicked.connect(partial(self._changeicon, index_i=i))

    def _get_item_text(self, item:QListWidgetItem)->str:
        index_f = item.data(Qt.UserRole)
        return self.label_l[index_f].text()
    
    def _getbutton(self, item:QListWidgetItem) -> QPushButton:
        index_f = item.data(Qt.UserRole)
        return self.button_l[index_f]
class AssociateList(UIAS):
    transfer_task = Signal(dict)
    def __init__(self, config:Config_Manager, parent:Union[QMainWindow, QWidget],manager:LauncherPathManager):  
        super().__init__(config, parent, manager)
        self.raise_()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.right_click)
        self.itemClicked.connect(self.left_click)
    
    def update_associated_words(self, text:str):
        if is_path(text):
            sign_n = 'path'
            matching_words, type_l = self.ass.ass_path(text)
            matching_words.insert(0, '..')
            type_l.insert(0, 'back')
        else:
            sign_n = 'name'
            matching_words, type_l = self.ass.ass_name(text)
        num_n = len(self.item_l)
        match_num = len(matching_words)
        if  num_n< match_num:
            for iti in range(match_num-num_n):
                item_i, button_i, label_i = self._init_signle_item(self.button_height, index_f=len(self.item_l))
                self.item_l.append(item_i)
                self.button_l.append(button_i)
                self.label_l.append(label_i)
        num_t = len(self.item_l)
        for i in range(num_t):
            if i >= len(matching_words):
                self.item_l[i].setHidden(True)
                continue
            self.item_l[i].setHidden(False)
            text_i = matching_words[i]
            icon_i = self._geticon(text_i, sign_n, type_l[i])
            self.label_l[i].setText(text_i)
            self.button_l[i].setIcon(AIcon(icon_i))

        # font_metrics = QFontMetrics(self.font())
        # b_h = self.config[self.button_height]
        # e_w = self.config[self.extra_width]
        # extra_size = b_h + e_w
        # if matching_words:
        #     max_len = max(13, max([len(i) for i in matching_words]))
        #     extra_size = int(e_w*max_len)
        #     width_f = max([font_metrics.boundingRect(' '+word).width() + extra_size for word in matching_words])
        # else:
        #     extra_size = int(self.extra_width*13)
        #     width_f = font_metrics.boundingRect("RemoteDesktop").width() + extra_size
    
    def _tab_complete(self, current_text:str):
        return self.ass.fill(current_text)
    
    def left_click(self, item):
        item_text = self._get_item_text(item)
        prompt_f = self._get_prompt()
        if is_path(prompt_f):
            if not self.path_manager.check(prompt_f):
                prompt_f = os.path.dirname(prompt_f)
            if item_text != '..':
                path_n = os.path.join(prompt_f, item_text)
                if '/' in prompt_f:
                    path_n = path_n.replace('\\', '/')
            else:
                path_n = os.path.dirname(prompt_f)
            self.up.input_box.setText(path_n)
        item.setSelected(False)
    
    def right_click(self, pos):
        prompt_f = self._get_prompt() 
        if not is_path(prompt_f):
            return 
        item = self.itemAt(pos)
        context_menu = QMenu(self)
        down_action = QAction('Downdload', self)
        downdir_action = QAction('Download to DIR', self)
        change_icon_action = QAction("Change Default Icon")
        down_action.triggered.connect(lambda: self._download(item, ask_save_dir=True))
        downdir_action.triggered.connect(lambda: self._download(item, ask_save_dir=False))
        change_icon_action.triggered.connect(lambda: self._cg_default_icon(item))
        context_menu.addAction(down_action)
        context_menu.addAction(downdir_action)
        context_menu.addAction(change_icon_action)
        context_menu.exec_(self.mapToGlobal(pos))

    def _transfer_trigger(self):
        pass

    def _cg_default_icon(self, item):
        pass


    def _upload(self, src:Union[str, list]):
        prompt_text = self._get_prompt()
        if not is_path(prompt_text):
            return
        if not self.path_manager.check(prompt_text):
            prompt_text = os.path.dirname(prompt_text)
        if not self.path_manager.isdir(prompt_text):
            return
        if isinstance(src, str):
            src = [src]
        src = [i for i in src if os.path.exists(i)]
        if src:
            self._transfer_preprocess({'src':src, 'dst':prompt_text, 'task_type':'upload',
                                    'host':self.up.HOST, 'host_type':self.path_manager.host_type})
    
    def _download(self, item, ask_save_dir:bool):
        if ask_save_dir:
            dir_path = QFileDialog.getExistingDirectory(self, "Choose a directory to save the file", self.filelog_default_path)
            if not dir_path:
                return
        else:
            dir_path = self.download_dir
        item_text = self._get_item_text(item)
        prompt_f = self._get_prompt()
        if not self.path_manager.check(prompt_f):
            prompt_f = os.path.dirname(prompt_f)
        src = os.path.join(prompt_f, item_text)
        if os.path.isdir(dir_path) and self.path_manager.check(src):
            file_type = 'dir' if self.path_manager.isdir(src) else 'file'
            self._transfer_preprocess({'src':[src], 'dst':dir_path, 'task_type':'download', 
                                     'host':self.up.HOST, 'host_type':self.path_manager.host_type})

    def _transfer_preprocess(self, tasks:dict):
        task_tupe_list = [] # [(src, dst, size), ...]
        type_t = tasks['task_type']
        host = tasks['host']
        host_type = tasks['host_type']
        if type_t == 'upload' or host_type != 'Remote':
            # src in upload task is a list of local directories or files
            # dst is a Local or Remote directory
            for src_i in tasks['src']:
                if os.path.isdir(src_i):
                    for dirpath, dirnames, filenames in os.walk(src_i):
                        for filename_i in filenames:
                            src = os.path.join(dirpath, filename_i)
                            dst = os.path.join(tasks['dst'], os.path.relpath(dirpath, src_i), filename_i)
                            size_f = os.path.getsize(src)
                            task_tupe_list.append((src, dst, size_f))
                else:
                    size_f = os.path.getsize(src_i)
                    task_tupe_list.append((src_i, os.path.join(tasks['dst'], os.path.basename(src_i)), size_f))
        else:
            for src_i in tasks['src']:
                for relpath, filename, file_path, size_i in self.path_manager.walk(src_i):
                    dst = os.path.join(tasks['dst'], relpath, filename)
                    task_tupe_list.append((file_path, dst, size_i))
        self.transfer_task.emit({'tasks':task_tupe_list, 'task_type':type_t, 'host':host, host_type:host_type})



    def _local_transfer(self, src:str, dst:str):
        bar = self.up.download_progress_bar
        if os.path.isfile(src):
            size_f = os.path.getsize(src)
            asyncio.run(self.copy_directory([(src, dst, size_f)], bar))
        elif os.path.isdir(src):
            tasks_f = self.src_dst_parsing(src, dst, 'local')
            size_f = sum([i[2] for i in tasks_f])
            asyncio.run(self.copy_directory(tasks_f, bar))
        else:
            return

    def _remote_transfer(self, src:str, dst:str, type_f:Literal['put', 'get']):
        bar = self.up.download_progress_bar
        if type_f == "put":
            tasks = self.src_dst_parsing(src, dst, 'local', 'remote')
            size_a = sum([i[2] for i in tasks])
            asyncio.run(self.transfer_multiple_files(tasks, type_f))
        else:
            tasks = self.src_dst_parsing(src, dst, 'remote', 'local')
            size_a = sum([i[2] for i in tasks])
            asyncio.run(self.transfer_multiple_files(tasks, type_f))

    def src_dst_parsing(self, src:str, dst:str, src_type:Literal['local', 'remote'], dst_type:Literal['local', 'remote'])->list:
        copy_paths = []  
        if src_type == 'local':
            for dirpath, dirnames, filenames in os.walk(src):
                relative_path = os.path.relpath(dirpath, src)
                target_dir = os.path.join(dst, relative_path)  
                if dst_type == 'local':
                    if not os.path.exists(target_dir):
                        os.makedirs(target_dir)
                else:
                    try:
                        self.remote_server.mkdir(target_dir)
                    except Exception as e:
                        pass
                for filename in filenames:
                    src_file = os.path.join(dirpath, filename)  
                    dst_file = os.path.join(target_dir, filename)  
                    file_size = os.path.getsize(src_file)
                    copy_paths.append((src_file, dst_file, file_size))
        else:
            walk_out = self.remote_server.walk(src)
            if not walk_out:
                return []
            for relpath, type, size_f in walk_out:
                if type == 'directory':
                    target_dir = os.path.join(dst, relpath)
                    os.makedirs(target_dir, exist_ok=True)
                else:
                    src_file = os.path.join(src, relpath)
                    dst_file = os.path.join(dst, os.path.basename(src), relpath)
                    copy_paths.append((src_file, dst_file, size_f))
        return copy_paths
     
    async def copy_directory(self, task_i:tuple, bar:QProgressBar):
        tasks = []  
        for src_i, dst_i, size_i in task_i:
            chunck_size = self.cal_chunck_size(size_i, hosttype='local')
            tasks.append(copy_file_chunk(src_i, dst_i, chunck_size, bar))
        await asyncio.gather(*tasks) 
    
    def progress_handler(self, current, total):
        print(f"上传进度：{current}/{total} bytes ({(current / total) * 100:.2f}%)")
    
    async def transfer_single_file(self, src, dst, size_f, sftp, type_f:Literal['get', 'put']):
        block_size = self.cal_chunck_size(size_f)
        if type_f == 'get':
            await sftp.get(src, dst, progress_handler=self.progress_handler, block_size= block_size)
        else:
            await sftp.put(src, dst, progress_handler=self.progress_handler, block_size= block_size)

    async def transfer_multiple_files(self, tasks:List[tuple[str, str]], type_f:Literal['get', 'put']):
        host_d = self.remote_server.host
        try:
            async with asyncssh.connect(host_d['HostName'], 
                                        username=host_d.get('User', os.getlogin()), 
                                        password=host_d.get(('Password', '')),
                                        port=int(self.host.get('port', 22))) as conn:
                async with conn.start_sftp_client() as sftp:
                    tasks = []  
                    for src, dst, size_f in tasks:
                        tasks.append(self.transfer_single_file(src, dst, sftp, type_f))
                    await asyncio.gather(*tasks)
                    return True
        except Exception as e:
            print(f"文件传输失败: {e}")
            return False

class PathModeSwitch2(QComboBox):
    def __init__(self, parent:QMainWindow, config:Config_Manager) -> None:
        super().__init__(parent)
        self.up = parent
        self.name = "path_mode_switch"
        self.config = config.deepcopy()
        self.config.group_chose(mode="Launcher", widget=self.name, obj=None)
        self.height_f = atuple('Launcher', self.name, 'Size', 'height')
        self.font_f = atuple('Launcher', self.name, 'font', 'main')
        self._load()
        self._initUI()
        UIUpdater.set(alist(self.height_f, self.font_f), self._loadconfig, alist(None, 'font'))
        self.currentIndexChanged.connect(self._index_change)
        self._index_change()
    
    def _loadconfig(self, height_f, font_f):
        self.setFixedHeight(height_f)
        self.setFont(font_f)
    
    def _load(self):
        self.path_manager:PathManager = self.up.path_manager
        self.hostd = self.path_manager.hostd
        self.mode_list = list(self.hostd.keys())
        self.pre = atuple('Launcher', self.name)
    
    def _initUI(self):
        for model_if in self.mode_list:
            self.addItem(model_if)
        self.setCurrentIndex(0)
        font_metrics = QFontMetrics(self.font())
        w_f = font_metrics.boundingRect(self.mode_list[0]).width() + 60  
        self.setFixedWidth(w_f)
        UIUpdater.set(self.pre|atuple('style'), self.customStyle)   
    
    def customStyle(self, config):
        box_config = config.get('box', {})
        menu_config = config.get('menu', {})
        b_bg = box_config.get('normal_background', 'rgba(255, 255, 255, 50)')
        b_font_color = box_config.get('font_color', '#F7F7F7')
        b_border = box_config.get('border', 'none')
        b_radius = box_config.get('border_radius', 10)
        b_padding = box_config.get('padding', [5,0,5,5])

        m_font_color = menu_config.get('font_color', '#F7F7F7')
        m_bg = menu_config.get('background', '#9DCDC8FF')
        m_hover_bg = menu_config.get('line_hover_background', '#4CC1B5')
        m_hover_font_color = menu_config.get('hover_font_color', 'black')
        self.box_style_dict = {
            'QComboBox':{
                'background': b_bg,
                'color': b_font_color,
                'border': b_border,
                'border-radius': f"{b_radius}px",
                "padding": f"{b_padding[2]}px {b_padding[1]}px {b_padding[3]}px {b_padding[0]}px", 
            },
            "QComboBox::drop-down":{
                'border': 'none'
            },
            }
        self.menu_style_dict = {
            'QComboBox QAbstractItemView':{
                'background-color': m_bg,
                'color': m_font_color,
                'selection-background-color': m_hover_bg,
                'selection-color': m_hover_font_color
            }
        }
        self.style_sheet_0 = style_make(self.box_style_dict)
        self.style_sheet_1 = style_make(self.menu_style_dict)
        self.setStyleSheet(self.style_sheet_0+'\n'+self.style_sheet_1)

    def _index_change(self):
        mode_n = self.currentText()
        font_metrics = QFontMetrics(self.font())
        min_length = font_metrics.boundingRect(self.mode_list[0]).width() + 60  
        w_f = max(font_metrics.boundingRect(mode_n).width() + 60  ,min_length)
        self.setFixedWidth(w_f)
    
    def _change_color(self, state_f:Literal['normal', 'error', 'warn']):
        color = self.config[self.pre|atuple('style', 'box', f'{state_f}_color')]
        if not color:
            color = "rgba(255, 255, 255, 50)" 
        self.box_style_dict['QComboBox']['background'] = color
        self.style_sheet_0 = style_make(self.box_style_dict)
        self.setStyleSheet(self.style_sheet_0+'\n'+self.style_sheet_1)
class PathModeSwitch(CustomComboBox):
    def __init__(self, parent:QMainWindow, config:Config_Manager) -> None:
        self.up = parent
        self.name = "path_mode_switch"
        self.config = config.deepcopy()
        self._load()
        super().__init__(modes=self.mode_list, style_d=self.style_d, box_height=self.box_height, 
                         menu_font=self.menu_font, box_font=self.box_font, parent=parent)
    
    def _load(self):
        self.path_manager:PathManager = self.up.path_manager
        self.hostd = self.path_manager.hostd
        self.mode_list = list(self.hostd.keys())
        self.pre = atuple('Launcher', self.name)
        self.style_d = atuple('Launcher', self.name, 'style')
        self.box_width = atuple('Launcher', self.name, 'Size', 'box_width')
        self.box_height = atuple('Launcher', self.name, 'Size', 'box_height')
        self.item_height = atuple('Launcher', self.name, 'Size', 'item_height')
        self.box_font = atuple('Launcher', self.name, 'font', 'box')
        self.menu_font = atuple('Launcher', self.name, 'font', 'menu')

    def setState(self, index_n:int):
        '''
        0: OK
        1: Connecting
        2: Error
        '''
        if not isinstance(index_n, int) and -1<index_n<3:
            return
        self.color_state = index_n
        self.box_w.color_state = index_n
        self.menu_w.color_state = index_n
        UIUpdater.action(self.style_d, self.box_w.customStyle)
        UIUpdater.action(self.style_d, self.menu_w.customStyle)

class InputBox(AutoEdit):   
    key_press = Signal(dict)
    geometry_signal = Signal(QRect)
    def __init__(self, parent:QMainWindow, config:Config_Manager):
        self.up = parent
        self.name = "input_box"
        self.height_f = atuple('Launcher', self.name, 'Size', 'height')
        self.font_f = atuple('Launcher', self.name, 'font', 'main')
        self.config = config.deepcopy()
        self.style_d = atuple('Launcher', self.name, 'style')
        super().__init__(text='', font=self.font_f, style_d=self.style_d, height=self.height_f)
        self.custom_keys = [Qt.Key_Tab, Qt.Key_Return, Qt.Key_Enter, Qt.Key_Up, Qt.Key_Down]
    
    def event(self, event:QEvent):
        match event.type():
            case QEvent.DragEnter:
                mime_data = event.mimeData()
                if mime_data.hasUrls():  
                    event.acceptProposedAction()  
                    return True  
                else:
                    return super().event(event)  
            case QEvent.DragMove:  
                mime_data = event.mimeData()
                if mime_data.hasUrls():
                    event.acceptProposedAction()  
                    return True  
                else:
                    return super().event(event)  
            case QEvent.Drop:  
                mime_data = event.mimeData()
                if mime_data.hasUrls():  
                    urls = mime_data.urls()
                    paths = [url.toLocalFile() for url in urls]  
                    self.key_press.emit({'type':'file_drop', 'paths':paths, "text":self.text()})
                    event.acceptProposedAction()
                    return True  
            case QEvent.KeyPress:
                if event.key() in self.custom_keys:
                    self.key_press.emit({'type':'key_press', 'key':event.key(), "text":self.text()})
                    return True
                else:
                    return super().event(event)
            case _:
                return super().event(event)
    
    def moveEvent(self, event):
        new_position = event.pos()
        self.geometry_signal.emit(QRect(new_position.x(), new_position.y(), self.width(), self.height()))
        super().moveEvent(event)  

    def resizeEvent(self, event):
        new_size = event.size()
        self.geometry_signal.emit(QRect(self.x(), self.y(), new_size.width(), new_size.height()))
        super().resizeEvent(event)  

class SearchTogleButton2(YohoPushButton):
    search_signal=Signal(dict) #{'url':str, 'sign':str}
    def __init__(self, parent, config:Config_Manager):
        self.up = parent
        self.name = "search_togle_button"
        config = config.deepcopy()
        icons = atuple('Launcher', self.name, 'icons')
        urls = atuple('Launcher', self.name, 'urls')
        sign = atuple('Launcher', self.name, 'sign')
        size = atuple('Launcher', self.name, 'Size', 'button_size')
        style_d = atuple('Launcher', self.name, 'style')

        self.url = config[urls][0]
        button_size = atuple('Launcher', self.name, 'Size', 'button_size')
        super().__init__(icon_i=config[icons][0], 
                         style_config=style_d,
                        size_f=button_size)
        UIUpdater.set(alist(icons, urls, sign), self._updateURL, alist())
        self.clicked.connect(self._click)
    
    def _updateURL(self, icons:atuple, urls:atuple, sign:atuple):
        self.urls = urls
        self.icons = icons[:len(urls)]
        self.sign = sign
        if self.url in self.urls:
            return 
        else:
            self.url = urls[0]
            self.setIcon(QIcon(self.icons[0]))
        
    def wheelEvent(self, event):
        delta = event.angleDelta().y()  # 获取鼠标滚轮的增量
        index_n = self.urls.index(self.url)
        if delta > 0:
            index_n = (index_n+1) % len(self.urls)
        elif delta < 0: 
            index_n = (index_n+len(self.icons)-1) % len(self.icons)
        self.url = self.urls[index_n]
        self.setIcon(AIcon(self.icons[index_n]))

    def _click(self):
        self.search_signal.emit({'url':self.url, 'sign':self.sign})

class SearchTogleButton(YohoPushButton):
    search_signal=Signal(dict) #{'url':str, 'sign':str}
    def __init__(self, parent, config:Config_Manager, input_box_geometry:QRect):
        self.up = parent
        self.name = "search_togle_button"
        config = config.deepcopy()
        icons = atuple('Launcher', self.name, 'icons')
        urls = atuple('Launcher', self.name, 'urls')
        sign = atuple('Launcher', self.name, 'sign')
        icon_proportion = atuple('Launcher', self.name, 'Size', 'icon_proportion')
        style_d = atuple('Launcher', self.name, 'style')

        self.url = config[urls][0]
        button_size = atuple('Launcher', self.name, 'Size', 'button_size')
        super().__init__(icon_i=config[icons][0], 
                         icon_proportion=icon_proportion,
                         style_config=style_d,
                        size_f=button_size,
                        parent=parent)
        UIUpdater.set(alist(icons, urls, sign), self._updateURL, alist())
        self.clicked.connect(self._click)
        self._update_geometry(input_box_geometry)
        self.show()
        self.raise_()

    def _updateURL(self, icons:atuple, urls:atuple, sign:atuple):
        self.urls = urls
        self.icons = icons[:len(urls)]
        self.sign = sign
        if self.url in self.urls:
            return 
        else:
            self.url = urls[0]
            self.setIcon(QIcon(self.icons[0]))
        
    def wheelEvent(self, event):
        delta = event.angleDelta().y()  # 获取鼠标滚轮的增量
        index_n = self.urls.index(self.url)
        if delta > 0:
            index_n = (index_n+1) % len(self.urls)
        elif delta < 0: 
            index_n = (index_n+len(self.icons)-1) % len(self.icons)
        self.url = self.urls[index_n]
        self.setIcon(AIcon(self.icons[index_n]))

    def _click(self):
        self.search_signal.emit({'url':self.url, 'sign':self.sign})
    
    def _update_geometry(self, input_box_geometry:QRect):
        x, y, w, h = input_box_geometry.getRect()
        x_n = x+w-self.width()
        self.setGeometry(x_n, y, self.width(), self.height())

class ShortcutButton(QWidget):
    launch_signal = Signal(str)
    def __init__(self, parent: QMainWindow, config:Config_Manager) -> None:
        super().__init__(parent)
        self.ctrl_pressed = False
        self.name = "shortcut_obj"
        self.up = parent
        self.config = config.deepcopy().group_chose(mode="Launcher", widget=self.name)
        self.layout_0 = amlayoutV(align_h='c')
        self.setLayout(self.layout_0)
        self.layout_0.setContentsMargins(0, 0, 0, 0)
        self._initpara()
        self._initUI()
        self.refresh()
        #self.setFixedSize(*self.config.get(None, widget="Size", obj=self.name)[-2:], )

    def _initpara(self):
        self.manager:ShortcutsPathManager = self.up.shortcut_data
        self.v_num = self.config[atuple('Launcher', 'shortcut_obj', 'vertical_button_num')]
        self.h_num = self.config[atuple('Launcher', 'shortcut_obj', 'horizontal_button_num')]
        self.icon_proportion = atuple('Launcher', 'shortcut_obj', 'Size', 'icon_proportion')
        self.num_exp = self.v_num * self.h_num

        self.df = self.manager.df
        self.num_real = self.df.shape[0]
        self.buttonlabel_list = []
        pre = ['Launcher', self.name]
        self.size_i = atuple(pre+['Size', 'button_r'])

        self.font_i = atuple(pre+['font', 'button_title'])
        self.style_d = atuple(pre+['style', 'shortcut_button'])
        self.button_label_style = atuple(pre+['style', 'button_label'])
        
    def _launch(self):
        button = self.sender()
        path = button.property('path')
        self.launch_signal.emit(path)
        try:
            os.startfile(path)
        except Exception as e:
            print(e) 
    
    def _initUI(self):
        index_f = 0
        for v_i in range(self.v_num):
            layout_if = QHBoxLayout()
            layout_if.setAlignment(Qt.AlignCenter)
            for h_i in range(self.h_num):
                name = ""
                icon = self.config.get('default_button_icon', obj='path')
                path = ''
                layout_i = QVBoxLayout()
                button_i = YohoPushButton(icon_i=icon, style_config=self.style_d, size_f=self.size_i, an_time=150, icon_proportion=self.icon_proportion)
                button_i.setProperty('path', path)
                label_i = AutoLabel(text=name, font=self.font_i, style_config=self.button_label_style)
                button_i.clicked.connect(self._launch)
                self.buttonlabel_list.append((button_i, label_i))
                layout_i.addWidget(button_i)
                layout_i.addWidget(label_i)
                layout_if.addLayout(layout_i)
                index_f += 1
            self.layout_0.addLayout(layout_if)                    

    def refresh(self):
        index_f = 0
        for v_i in range(self.v_num):
            for h_i in range(self.h_num):
                if index_f < self.num_real:
                    name, _, path = self.df.iloc[index_f, 0:3]
                    icon = self.manager.geticon(name)
                if isinstance(icon, atuple):
                    icon = self.config[icon]
                button_i, label_i = self.buttonlabel_list[index_f]
                button_i.setProperty('path', path)
                button_i.setIcon(QIcon(icon))
                label_i.setText(name)
                index_f += 1

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.ctrl_pressed = True
    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.ctrl_pressed = False
    def wheelEvent(self, event):
        if not self.ctrl_pressed:
            return
        # use wheel to resize the button
        if event.angleDelta().y() > 0:
            factor_i = 1.1
        else:
            factor_i = 0.9
        for button_i, label_i in self.buttonlabel_list:
            pix_size = label_i.font().pixelSize()
            label_i.font().setPixelSize(int(pix_size*factor_i))
            size_ori = button_i.size()
            button_i._resize([int(size_ori.width()*factor_i), int(size_ori.height()*factor_i)])

class TransferProgress(ProgressBar):
    def __init__(self, parent, max_value, height):
        self.up = parent
        super().__init__(parent, max_value, height)

class ProgressData:
    def __init__(self, src:str, dst:str, src_host:str, dst_host:str, total_size:int):
        self.src = src
        self.dst = dst
        self.src_host = src_host
        self.dst_host = dst_host
        self.total_size = total_size
        random_num = random.randint(0, 1000000)
        self.ID = hash(tuple(src, dst, total_size, random_num))
        self.progress = 0

class ProgressWidget2(QWidget):
    def __init__(self, parent, config:Config_Manager, data:dict):
        self.up = parent
        super().__init__()
        self.data_l = []

    def _loadConfig(self):
        self.bar_height = atuple('Launcher', 'progress_widget', 'Size', 'bar_height')
        self.info_height = atuple('Launcher', 'progress_widget', 'Size', 'info_height')
        self.label_font = atuple('Launcher', 'progress_widget', 'font', 'label_font')
        self.src_label_bkg = atuple('Launcher', 'progress_widget', 'color', 'src_label_background')
        self.dst_label_bkg = atuple('Launcher', 'progress_widget', 'color', 'dst_label_background')
        self.arrow_icon = atuple('Launcher', 'progress_widget', 'path', 'arrow_icon')
        self.close_icon = atuple('Launcher', 'progress_widget', 'path', 'close_icon')

    def _initUI(self):
        # total layout
        self.layout_0 = amlayoutV()
        self.setLayout(self.layout_0)

        # left layout
        self.layout_up = amlayoutH()
        # right layout
        self.layout_down = amlayoutH()
        add_obj(self.layout_up, self.layout_down, parent_f=self.layout_0)

        self.bar = ProgressBar(self, self.data['max_value'], self.bar_height)
        self.progress_label = AutoLabel(self.progress, self.label_font)

        add_obj(self.bar, self.progress_label, parent_f=self.layout_up)

        self.label_src = AutoLabel(text=self.src, font=self.label_font, color=self.src_label_bkg, height=self.info_height)
        self.label_dst = AutoLabel(text=self.dst, font=self.label_font, color=self.dst_label_bkg, height=self.info_height)

        self.arrow = AutoLabel(text='',icon_f=self.arrow_icon, height=self.info_height)

        self.close_button = YohoPushButton(self.close_icon, self.info_height, "shake", an_time=90)
        self.close_button.clicked.connect(self._terminate)
        add_obj(self.label_src, self.arrow, self.label_dst, parent_f=self.layout_down)
        self.layout_down.addStretch(1)
        self.layout_down.addWidget(self.close_button)

    def update(self, size_transfered:int):
        self.size_transfered += size_transfered
        self.progress = self.size_transfered/self.total_task
        self.bar.setValue(self.progress)
        self.progress_label.setText(f"{self.progress:.2f}%")

    def _terminate(self):
        pass
    
    def add(self, data:ProgressData):
        pass

class ProgressWidget(QWidget):
    kill_signal = Signal(int)
    add_signal = Signal(ProgressData)
    update_signal = Signal(dict)
    def __init__(self, parent,):
        self.up = parent
        super().__init__()
        self._loadConfig()
        self._initUI()
        UIUpdater.set(self.main_height, self.setFixedHeight)
        self.data_l = []
        self.tipTimer = QTimer(self)
        self.tipTimer.setSingleShot(True)
        self.tipTimer.timeout.connect(self._showTip)

    def _loadConfig(self):
        self.bar_height = atuple('Launcher', 'progress_widget', 'Size', 'bar_height')
        self.arrow_icon = atuple('Launcher', 'progress_widget', 'path', 'arrow_icon')
        self.close_icon = atuple('Launcher', 'progress_widget', 'path', 'close_icon')
        self.bar_style = atuple('Launcher', 'progress_widget', 'style', 'bar')
        self.icon_size = atuple('Launcher', 'progress_widget', 'Size', 'icon_size')
        self.icon_style = atuple('Launcher', 'progress_widget', 'style', 'close_button')
        self.main_style = atuple('Launcher', 'progress_widget', 'style', 'main')
        self.main_tip_style = atuple('Launcher', 'progress_widget', 'style', 'main_tip')
        self.main_height = atuple('Launcher', 'progress_widget', 'Size', 'widget_height')

    def _initUI(self):
        # total layout
        self.layout_0 = amlayoutH(align_v='c')
        self.layout_0.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout_0)

        self.bar = ProgressBar(parent=self, style_d=self.bar_style, max_value=100, height=self.bar_height)
        self.close_button = YohoPushButton(icon_i=self.close_icon, style_config=self.icon_style, size_f=self.icon_size)
        add_obj(self.bar, self.close_button, parent_f=self.layout_0)

    @Slot(int)
    def update(self, data_f:dict[Literal['ID', 'size']]):
        pass

    def loadData(self, data:ProgressData):
        pass

    def kill(self, data:ProgressData):
        pass
    
    def add(self, data:ProgressData):
        pass

    def enterEvent(self, event):
        self.tipTimer.start(1000)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.tipTimer.stop()
        super().leaveEvent(event)

    def _showTip(self):
        pass

class ProgressWidgetManager(QStackedWidget):
    def __init__(self, parent:QWidget, config:Config_Manager):
        super().__init__(parent)
        self.name = 'progress_widget'
        self.up = parent
        self.config = config.deepcopy().group_chose(mode="Launcher", widget=self.name)
    
    def _load(self):
        self.bar_height = self.config.get('bar_height', obj='Size')
        self.info_height = self.config.get('info_height', obj='Size')

        self.label_font = self.config.get('label_font', obj='font')

        self.srclabel_bkglabel_bkg = self.config.get('src_label_background', obj='color')
        self.dstlabel_bkg = self.config.get('dst_label_background', obj='color')

        self.arrow_icon = QIcon(self.config.get('arrow_icon', obj='path'))
        self.close_icon = QIcon(self.config.get('close_icon', obj='path'))

    def _add_widget(self, data:dict):
        widget = ProgressWidget(self.up, self.config, data)
        self.addWidget(widget)
        return widget


