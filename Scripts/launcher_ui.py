import os
import sys
from toolbox import *
from PySide2.QtWidgets import QListWidget, QMainWindow, QWidget,QListWidgetItem,QPushButton, QHBoxLayout, QVBoxLayout, QLabel
from PySide2.QtGui import QFontMetrics, QIcon
from PySide2.QtCore import QSize, Qt
from .p_widget import *
from functools import partial
import shutil
import pandas
import pathlib
import aiofiles
import asyncio
import asyncssh
from typing import List, Literal, Union, OrderedDict

async def copy_file_chunk(src:str, dst:str, chunk_size:int, bar:QProgressBar):
    async with aiofiles.open(src, 'rb') as fsrc, aiofiles.open(dst, 'wb') as fdst:
        while True:
            chunk = await fsrc.read(chunk_size)
            if not chunk:
                break  
            await fdst.write(chunk)
            # update progress bar here 

class Associate:
    def __init__(self, nums:int, 
                 program_info_df:pandas.DataFrame):
        self.num = nums
        self.df = program_info_df
        self.df = self.df.fillna(value="")
        self.names = nan_to_sign(list(self.df['Name'].values))
        self.ch_names = nan_to_sign(list(self.df['Chinese Name'].values))
        self.description = nan_to_sign(list(self.df['Description'].values))
        self.exe_path = nan_to_sign(list(self.df['EXE Path'].values))
        #self.icon_path = nan_to_sign(list(self.df['Icon Path'].values))
    # To Associate subdirectory of certain path
    def path(self, prompt_f):
        if not prompt_f:
            return []
        path_f = pathlib.Path(prompt_f)
        # prompt is a specific file path
        if path_f.exists and path_f.is_file():
            return []
        # prompt is a directory
        if os.path.exists(prompt_f):
            list_1 = os.listdir(prompt_f)
            list_2 = []
            for name_i in list_1:
                if os.path.isdir(os.path.join(prompt_f, name_i)):
                    list_2.append('dir')
                else:
                    list_2.append('file')
            return list_1, list_2
        sup_path = path_f.parent
        dir_name_n = path_f.name
        if not sup_path.exists():
            return []
        else:
            list_1f = sorted([dir_if for dir_if in os.listdir(sup_path) if dir_name_n in dir_if], key=lambda x:x.index(dir_name_n))
            list_2f = sorted([dir_if for dir_if in os.listdir(sup_path) if dir_name_n.lower() in dir_if.lower()], key=lambda x:(x.lower()).index(dir_name_n.lower()))
            list_1 = rm_dp_list_elem(list_1f+list_2f, reverse=False)
            list_2 = []
            for name_i in list_1:
                if os.path.isdir(os.path.join(prompt_f, name_i)):
                    list_2.append('dir')
                else:
                    list_2.append('file')
            return list_1, list_2
    
    # To associate a programme name of prompt
    def name(self, prompt_f):
        if not prompt_f:
            return []
        output_name = sorted([name_i for name_i in self.names if prompt_f.lower() in name_i.lower()], key=lambda s: (s.lower().index(prompt_f.lower()))/len(s))
        output_chname = sorted([ch_name_i for ch_name_i in self.ch_names if prompt_f.lower() in ch_name_i.lower()], key=lambda s: (s.lower().index(prompt_f.lower()))/len(s))
        output_des = [self.names[self.description.index(dsp_name_i)] for dsp_name_i in self.description if prompt_f.lower() in dsp_name_i.lower()]
        output_chname_t = [i for i in output_chname if self.names[self.ch_names.index(i)] not in output_name]
        output_des_t = [i for i in output_des if self.ch_names[self.names.index(i)] not in output_chname]
        return rm_dp_list_elem(output_name+output_chname_t+output_des_t, reverse=False)[0:self.num], ['app']*len(output_name)+['ch_name']*len(output_chname_t)+['description']*len(output_des_t)
    
    # To associate programmes with multiple prompts
    def multi_pro_name(self, prompt_list_f):
        output_0 = list_overlap([self.name(prompt_if)[0] for prompt_if in prompt_list_f])
        output_1 = [self.names[(self.ch_names).index(ch_name_i)] for ch_name_i in list_overlap([self.name(prompt_if)[1] for prompt_if in prompt_list_f])]
        output_2 = [self.names[(self.description.index(dsp_name_i))] for dsp_name_i in list_overlap([self.name(prompt_if)[2] for prompt_if in prompt_list_f])]
        return (output_0+output_1+output_2)[0:self.num]
    
    # Automatically complete PATH
    def fill_path(self, prompt_f):
        # if prompt is a exsisting path
        if os.path.exists(prompt_f):
            if len(os.listdir(prompt_f))==1:
                return os.path.join(prompt_f, os.listdir(prompt_f)[0], os.sep)
            else:
                return None
        else:
            sup_path = os.path.dirname(prompt_f)
            if not os.path.exists(sup_path):
                return None
            else:
                name_wait_list = [name_if for name_if in os.listdir(sup_path) if (name_if).lower().startswith((prompt_f.split('\\')[-1]).lower())]
                if len(name_wait_list) == 1:
                    return os.path.join(sup_path, name_wait_list[0], os.sep)
                else:
                    return None
    # Automatically complete Remote PATH

    # Automatically complete Name
    def fill_name(self, prompt_f):
        output_0 = [name_i for name_i in self.names if name_i.lower().startswith(prompt_f.lower())]
        output_1 = [ch_name_i for ch_name_i in self.ch_names if ch_name_i.lower().startswith(prompt_f.lower())]
        if len(output_0) == 1:
            return output_0[0]
        elif len(output_1) == 1:
            return output_1[0]

class AssociateList(QListWidget):
    def __init__(self, config:Config_Manager, parent:Union[QMainWindow, QWidget],manager:LauncherPathManager):  
        super(AssociateList, self).__init__(parent)
        self.up = parent
        self.name = "associate_list"
        self.config = config.deepcopy()
        self.manager = manager
        # set Data
        self._load()
        # init
        self._setStyle()
        self._inititems()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.right_click)
        self.itemClicked.connect(self.left_click)
    
    def focusNextPrevChild(self, next):
    # inhibit focus move when pressing TAB
        # Override to prevent normal focus change
        return True
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():  
            event.acceptProposedAction()  
    def dragMoveEvent(self, event):
        event.accept()
    def dropEvent(self, event: QDropEvent):
        mime_data = event.mimeData()
        if mime_data.hasUrls():  
            urls = mime_data.urls()  
            paths_t = []
            for url in urls:
                paths_t.append(url.toLocalFile())
            self._upload(self, paths_t)
            event.acceptProposedAction()  
    
    def _load(self):
        self.config.group_chose("Launcher", self.name)
        self.num = self.config.get("max_exe_num", )
        self.max_num = self.config.get("max_dir_num", )
        self.launcher_df = self.manager.df
        self.ass = Associate(self.num, self.launcher_df)
        
        self.config.group_chose(mode="Launcher", widget=self.name, obj=None)

        self.local_min_chunck = int(self.config.get('local_min_chunck')*1024*1024)
        self.remote_min_chunck = int(self.config.get('remote_min_chunck')*1024*1024)
        self.local_max_chunck = int(self.config.get('local_max_chunck')*1024*1024)
        self.remote_max_chunck = int(self.config.get('remote_max_chunck')*1024*1024)
        
        self.download_dir = self.config.get("download_save_dir", obj="path")
        self.exe_icon_getter = self.config.get('exe_icon_getter', obj='path')
        self.file_icon_getter = self.config.get('file_icon_getter', obj='path')
        self.max_length = self.config.get("max_length")

        self.font_a = self.config.get('main', obj='font')
        
        
        self._load_default_icons()
        self.remote_server:SshManager=None

    def _load_default_icons(self) -> dict:
        self.file_icon_folder = self.config.get('file_icon_folder', mode="Launcher", widget=self.name, obj="path")
        
        self.file_icon_d = {}
        for name_i in os.listdir(self.file_icon_folder):
            name, ext = os.path.splitext(name_i)
            self.file_icon_d[name] = QIcon(os.path.join(self.file_icon_folder, name_i))
        
        default_folder_icon = QIcon(self.config.get('default_folder_icon', mode="Launcher", widget=self.name, obj="path"))
        default_file_icon = QIcon(self.config.get('default_file_icon', mode="Launcher", widget=self.name, obj="path"))
        self.default_icon_d = {'dir':default_folder_icon, 'file':default_file_icon}
    
    def _setStyle(self):
        self.setFont(self.font_a)
        #associate_list_set = tuple(self.config.get(self.name, widget="Size", obj=None))
        self.setSizeAdjustPolicy(QListWidget.AdjustToContents)
        self.setStyleSheet("""
        QListWidget {
                border: 3px solid black; /* 设置边框 */
            }
            
        QListView {
            background: transparent;  /* 设置背景颜色 */
            border: 10px solid #CCCCCC;  /* 设置边框 */
            border-radius: 20px;  /* 设置边角弧度 */
        }

        QListView::item {
            border: none;
            padding:1px;  /* 设置每个项的内边距 */
            background-color: #FFFFFF;  /* 设置背景颜色 */
            border-radius: 10px;  /* 设置边角弧度 */
        }
        
        QListView::item:hover {
            background-color: #FFA98F;  /* 设置悬停时的背景颜色 */
        }
        
        QListView::item:selected {
            background-color: #14B699;  /* 设置选中项的背景颜色 */
            color: white;  /* 设置选中项的文字颜色 */
        }
        """)
        self.horizontalScrollBar().setStyleSheet("""
        QScrollBar:horizontal {
            background: transparent;
            height: 30px;
            margin: 3px;
        }

        QScrollBar::handle:horizontal {
            background: #32CC99;
            min-width: 80px;
            border-radius: 10px;
        }

        QScrollBar::sub-line:horizontal,
        QScrollBar::add-line:horizontal,
        QScrollBar::sub-page:horizontal,
        QScrollBar::add-page:horizontal,
        QScrollBar::sub-line:vertical,
        QScrollBar::add-line:vertical,
        QScrollBar::sub-page:vertical,
        QScrollBar::add-page:vertical,
        QScrollBar::sub-line:corner,
        QScrollBar::add-line:corner {
        background: transparent;
        }
        """)
        self.setSpacing(1)  # 设置 item 之间的间距为 10 像素
        self.setAttribute(Qt.WA_TranslucentBackground) 
    
    def cal_chunck_size(self, size_f:int, hosttype:Literal['local', 'remote'])->int:
        if hosttype == 'local':
            return min(max(self.local_min_chunck, size_f//48), self.local_max_chunck)
        else:
            return min(max(self.remote_min_chunck, size_f//48), self.remote_max_chunck)

    def _changeicon(self, index_i):
        app_name = self.labels[index_i].text
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
        self.buttons[index_i].setIcon(QIcon(dst))
    
    def _init_signle_item(self, button_size:QSize, index_f:int,label_font:QFont=None):
        label_font = self.font() if label_font is None else label_font
        item_i = QListWidgetItem()
        item_i.setData(Qt.UserRole, int(index_f))
        button_i = YohoPushButton(self.default_icon_d['dir'], button_size, an_type="shake")
        label_i = AutoLabel(text="Default", font=label_font)
        widget_i = QWidget()
        layout_i = QHBoxLayout()
        layout_i.addWidget(button_i)
        layout_i.addWidget(label_i)
        widget_i.setLayout(layout_i)
        self.setItemWidget(item_i, widget_i)
        return item_i, button_i, widget_i

    def _inititems(self):
        het = self.config.get(name_f="het", mode="Common", widget="Size", obj=None)
        button_size = QSize(het, het)
        self.button_l = []
        self.label_l = []
        self.item_l = []
        for i in range(self.max_num):
            item_i, button_i, label_i = self._init_signle_item(button_size, i)
            self.addItem(item_i)
            item_i.setHidden(True)
            self.item_l.append(item_i)
            self.button_l.append(button_i)
            self.label_l.append(label_i)
            button_i.clicked.connect(partial(self._changeicon, index_i=i))
    
    def _geticon(self, name:str, sign:Literal['name', "path"], type_f:Literal["dir", 'file'])->QIcon:
        match sign:
            case "name":
                return self.manager.get_icon(name)
            case _:
                if type_f == 'dir':
                    return self.default_icon_d['folder']
                else:
                    name_i, ext = os.path.splitext(name) 
                    icon = self.file_icon_d.get(ext.lstrip('.'), None)
                    if icon:
                        return icon
                    else:
                        return self.default_icon_d['file']
    
    def _get_item_text(self, item:QListWidgetItem)->str:
        index_f = item.data(Qt.UserRole)
        return self.label_l[index_f].text()
    
    def _get_input_text(self)->str:
        match self.up.HOST:
            case "wsl":
                return self.wsl_location+self.input_box.text().strip()
            case _:
                return self.input_box.text().strip()

    def _check_path(self, path_t:str):
        match self.up.HOST:
            case "remote":
                check_r = self.remote_server.check_exist(path_t)
                match check_r:
                    case "file":
                        return 0
                    case "directory":
                        return 1
                    case _:
                        return -1
            case _:
                if os.path.isfile(path_t):
                    return 0
                elif os.path.isdir(path_t):
                    return 1
                else:
                    return -1

    def _getbutton(self, item:QListWidgetItem) -> QPushButton:
        index_f = item.data(Qt.UserRole)
        return self.button_l[index_f]
    
    def left_click(self, item):
        prompt_f = 1
        pass
    
    def right_click(self, pos):
        prompt_f = self.up.input_box.text() 
        item = self.list_widget.itemAt(pos)
        if (("\\" not in prompt_f) and ('/' not in prompt_f)) or not item:
            return
        
        context_menu = QMenu(self)
        down_action = QAction('Downdload', self)
        downdir_action = QAction('Download to DIR', self)
        change_icon_action = QAction("Change Default Icon")
        down_action.triggered.connect(lambda: self._download(item, True))
        downdir_action.triggered.connect(lambda: self._download(item, False))
        change_icon_action.triggered.connect(lambda: self._cg_default_icon(item))
        context_menu.addAction(down_action)
        context_menu.addAction(downdir_action)
        context_menu.exec_(self.list_widget.mapToGlobal(pos))
    
    def _upload(self, src:str):
        prompt_text = self._get_input_text()
        dst = prompt_text if self._check_path(prompt_text) == 1 else os.path.dirname(prompt_text)
        if self._check_path(dst) != 1:
            return
        match self.up.HOST:
            case "local"| "wsl":
                self._local_transfer(src, dst)
            case "remote":
                tasks = self.src_dst_parsing(src, dst, 'local', 'remote')
                size_a = sum([i[2] for i in tasks])
                asyncio.run(self.transfer_multiple_files(tasks, 'put'))
    
    def _download(self, item, ask_save_dir:bool):
        if ask_save_dir:
            dir_path = QFileDialog.getExistingDirectory(self, "Choose a directory to save the file")
            if not dir_path:
                return
        else:
            dir_path = self.download_dir
        item_text = self._get_item_text(item)
        prompt_f = self._get_input_text()
        src = os.path.join(prompt_f, item_text)
        if self._check_path(src) == -1:
            src = os.path.join(os.path.dirname(prompt_f), item_text)
            src_check = self._check_path(src)
            if src_check == -1:
                return
        match self.up.HOST:
            case "local"|"wsl":
                self._local_transfer(src, dir_path)
            case _:
                if src_check == 0:
                    self._remote_transfer(src, dir_path)
                else:
                    dst = os.path.join(dir_path, os.path.basename(src))
                    size = self.remote_server.getsize(src)
                    if size != 0:
                        asyncio.run(self.transfer_single_file(src, dst, size, 'get'))
    
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
    
    def update_associated_words(self):
        if self.up.MODE != "Launcher":
            return
        current_text:str = self.up.get_input()
        match self.up.HOST:
            case "local":
                self._local_update(current_text)
            case _:
                self._remote_update(current_text)
    
    def _local_update(self, current_text:str):
        num_n = self.num
        sign_n = "name"
        if is_path(current_text):
            num_n = self.max_num
            sign_n = "local"
            matching_words, type_l = self.ass.path(current_text)
            matching_words = ['..'] + matching_words
            type_l = ['parent'] + type_l
        else:
            # if ';' not in current_text:
            matching_words, type_l = self.ass.name(current_text)
            # else:
            #     matching_words = self.ass.multi_pro_name(current_text.split(';'))

        for i in range(num_n):
            if i >= len(matching_words):
                self.item_l[i].setHidden(True)
                continue
            text_i = matching_words[i]
            icon_i = self._geticon(text_i, sign_n, type_l[i])
            self.labels[i].setText(text_i)
            self.buttons[i].setIcon(icon_i)
    
        font_metrics = QFontMetrics(self.font())
        width_f = max([font_metrics.boundingRect(' '+word).width() + 60 for word in matching_words])
        width_f = min(width_f, self.max_length)
        self.setMinimumWidth(width_f)
        self.setMaximumWidth(width_f)
    
    def _remote_update(self, current_text:str):
        if not self.remote_server:
            return
        est = self.remote_server.check_exist(current_text)
        dirlist = []
        match est:
            case "directory":
                dirlist = self.remote_server.list_files(current_text)
                match_word = ['..']+dirlist
            case "file":
                match_word = ['..']
            case _:
                est = self.remote_server.check_exist(os.path.dirname(current_text))
                match est:
                    case "directory":
                        dirlist = self.remote_server.list_files(est)
                        match_word = ['..']+dirlist
                    case _:
                        match_word = ['..']
        for i in range(self.max_num):
            if i >= len(match_word):
                self.item_l[i].setHidden(True)
                continue
            text_i = match_word[i]
            icon_i = self._geticon(text_i, "remote")
            self.labels[i].setText(text_i)
            self.buttons[i].setIcon(icon_i)

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
                                        port=int(self.host.get('Port', 22))) as conn:
                async with conn.start_sftp_client() as sftp:
                    tasks = []  
                    for src, dst, size_f in tasks:
                        tasks.append(self.transfer_single_file(src, dst, sftp, type_f))
                    await asyncio.gather(*tasks)
                    return True
        except Exception as e:
            print(f"文件传输失败: {e}")
            return False

class SwitchButton(QComboBox):
    def __init__(self, parent: QMainWindow, config:Config_Manager) -> None:
        super().__init__(parent)
        self.up = parent
        self.name = "switch_button"
        self.config = config.deepcopy()
        self.config.group_chose(mode="MainWindow", widget=self.name)
        self.mode_list = self.config.get("mode_list", mode="Common", widget=None, obj=None)
        self.gem = self.config.get(self.name, widget=None, obj="Size")
        self.currentIndexChanged.connect(self._index_change)  
        self._initUI()
    
    def _initUI(self):
        font_f = self.config.get("font", obj=None)
        self.setFont(font_f)
        for model_if in self.mode_list:
            self.addItem(model_if)
        self.setCurrentIndex(self.mode_list.index(self.up.MODE))

        font_metrics = QFontMetrics(self.font())
        w_f = font_metrics.boundingRect(self.up.MODE).width() + 30  
        #self.setFixedSize(w_f, self.gem[-1])
        self.setMaximumWidth(self.gem[-1])
        button_style = """
        QComboBox {
            background-color: rgba(255, 255, 255, 50);
            border: 0px solid #2980b9;
            border-radius: 10px;
            padding: 5px;
            color: white;
        }

        QComboBox::drop-down {
            border: none;  /* 移除下拉箭头的边框 */
        }
        
        QComboBox QAbstractItemView {
        border-radius: 0px;
        background-color:  qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #73B1A7, stop:1 #EDFFFF);
        border: 0px solid #CCCCCC; /* 下拉列表的边框 */
        color: black; /* 下拉列表的文本颜色 */
        selection-background-color: #4CC1B5; /* 选中项的背景颜色 */
        selection-color: black; /* 选中项的文本颜色 */
        }
        
        
        """
        self.setStyleSheet(button_style)
    
    def _index_change(self):
        mode_n = self.currentText()
        self.up.MODE = mode_n
        font_metrics = QFontMetrics(self.font())
        w_f = font_metrics.boundingRect(mode_n).width() + 30  
        self.setFixedSize(w_f, self.gem[-1])

class PathModeSwitch(QComboBox):
    def __init__(self, parent:QMainWindow, config:Config_Manager) -> None:
        super().__init__(parent)
        self.up = parent
        self.name = "path_mode_switch"
        self.config = config.deepcopy()
        self.config.group_chose(mode="Launcher", widget=self.name, obj=None)
        self._load()
        self._initUI()
        self.currentIndexChanged.connect(self._index_change)
    
    def _load(self):
        self.ssh_config_path = self.config.get('ssh_config', mode='Launcher', widget=None, obj='path')
        self.host_fliter = self.config.get('hostname')
        self.host_d = OrderedDict(parse_ssh_config(self.ssh_config_path, fliter=self.host_fliter))
        self.host_types = {key:"Remote" for key in self.host_d.keys()}
        self.wsl_d = self.config.get('wsl', mode='Launcher', widget=None, obj='path')
        
        self.host_d = OrderedDict({'Local':''}) | self.host_d
        self.host_types = {'Local':'Local'}| self.host_types
        if self.wsl_d:
            print(self.wsl_d)
            self.host_types = self.host_types | {key:"Local" for key in self.wsl_d.keys()}
            self.host_d = self.host_d | self.wsl_d
        self.mode_list = list(self.host_d.keys())
    
    def _initUI(self):
        self.gem = self.config.get(self.name, widget=None, obj="Size")
        font_f = self.config.get("font", obj=None)
        self.setFont(font_f)
        for model_if in self.mode_list:
            self.addItem(model_if)
        self.setCurrentIndex(self.mode_list.index(self.up.HOST))
        font_metrics = QFontMetrics(self.font())
        w_f = font_metrics.boundingRect(self.up.MODE).width() + 30  
        self.setFixedSize(w_f, self.gem[-1])
        button_style = """
        QComboBox {
            background-color: rgba(255, 255, 255, 50);
            border: 0px solid #2980b9;
            border-top-left-radius: 20px;
            border-bottom-left-radius: 20px;
            padding: 5px;
            color: white;
            margin: 0px;
        }
        QComboBox::drop-down {
            border: none;  /* 移除下拉箭头的边框 */
        }
        QComboBox QAbstractItemView {
        border-radius: 0px;
        background-color:  qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #73B1A7, stop:1 #EDFFFF);
        border: 0px solid #CCCCCC; /* 下拉列表的边框 */
        color: black; /* 下拉列表的文本颜色 */
        selection-background-color: #4CC1B5; /* 选中项的背景颜色 */
        selection-color: black; /* 选中项的文本颜色 */
        }
        """
        self.setStyleSheet(button_style)
    
    def _index_change(self):
        mode_n = self.currentText()
        self.up.HOST = mode_n
        self.up.HOST_TYPE = self.host_types[mode_n]
        font_metrics = QFontMetrics(self.font())
        w_f = font_metrics.boundingRect(mode_n).width() + 30  
        self.setFixedSize(w_f, self.gem[-1])
    
class TopButton(QWidget):
    def __init__(self, parent: QMainWindow, config:Config_Manager) -> None:
        super().__init__(parent)
        self.name = "top_button"
        self.up = parent
        self.config = config.deepcopy()
        self.config.group_chose(mode="MainWindow", widget=self.name)
        self.geom = self.config.get(self.name, widget=None, obj="Size")
        self.setFixedHeight(int(1.2*self.geom[-1]))
        self.max_state = False
        
        
    def _initbuttons(self):
        size_i = Asize(self.geom[-1], self.geom[-1])
        self.max_path = self.config.get('maximum', obj="path")
        self.min_path = self.config.get('minimum', obj="path")
        self.middle_path = self.config.get('middle', obj="path")
        self.close_path = self.config.get('close', obj="path")

        self.max_button = YohoPushButton(QIcon(self.max_path), size_i, 'shake')
        self.max_button.clicked.connect(self.max_click)
        self.min_button = YohoPushButton(QIcon(self.min_path), size_i, 'shake')
        self.close_button = YohoPushButton(QIcon(self.close_path), size_i, 'shake')
        return [self.min_button, self.max_button, self.close_button]

    def max_click(self):
        if self.max_state:
            self.max_button.setIcon(QIcon(self.middle_path))
            self.max_state = False
        else:
            self.max_button.setIcon(QIcon(self.max_path))
            self.max_state = True

class InputBox(QLineEdit):
    def __init__(self, parent:QMainWindow, config:Config_Manager):
        super().__init__(parent)
        self.up = parent
        self.name = "input_box"
        self.config = config.deepcopy()
        self._initUI()
        self.returnPressed.connect(self.clear)
    def _initUI(self):
        self.config.group_chose(mode=self.up.MODE, widget="input_box")
        sty_sheet = f'''
                border-top-right-radius: 20px;
                border-bottom-right-radius: 20px;
                padding-left: 20px;
                padding-right: 15px;
                margin: 0px;
        '''
        self.setStyleSheet(sty_sheet)  # smooth four angle
        # self.up.input_box.textChanged.connect(self.up.update_associated_words)
        # self.up.input_box.returnPressed.connect(self.up.confirm_action)
        self.setFont(self.config.get("main", obj="font"))
        gemo = self.config.get(self.name, widget=None, obj="Size")
        self.setFixedHeight(gemo[-1])

class SearchTogleButton(YohoPushButton):
    def __init__(self, parent, config:Config_Manager):
        self.up = parent
        self.name = "search_togle_button"
        self.config = config.deepcopy()
        self.config.group_chose(mode="Launcher", widget=self.name, obj=None)
        self.icons = self.config.get("icons")
        self.urls = self.config.get("urls")
        self.sign = self.config.get("sign")
        # self.setIcon(QIcon(self.icons[0]))
        self.url = self.urls[0]
        button_size = Asize(*self.config.get(self.name, widget=None, obj="Size"))
        super().__init__(icon_i=QIcon(self.icons[0]), 
                        size_f=button_size.q(), an_type="resize")
        self.setFixedSize(button_size)
    
        # self.setIconSize(self.icon_size)
        # self.setFixedSize(1.3*self.icon_size)
        # self.setStyleSheet("""
        #     QPushButton {
        #         border: none;
        #         background-color: transparent;
        #     }
        # """)
        # self.clicked.connect(self.print)
    def wheelEvent(self, event):
        delta = event.angleDelta().y()  # 获取鼠标滚轮的增量
        index_n = self.urls.index(self.url)
        if delta > 0:
            index_n = (index_n+1) % len(self.urls)
        elif delta < 0:
            index_n = (index_n+len(self.icons)-1) % len(self.icons)
        self.url = self.urls[index_n]
        self.setIcon(QIcon(self.icons[index_n]))

class SearchButton(YohoPushButton):
    def __init__(self, http_icon_tuple:tuple[str, QIcon], 
                 size:Union[int, QSize], 
                 an_type:Literal["shake", 'resize', None]=None, 
                 an_time:int=180,
                 change_size:float=0.6,
                 change_period:float=0.7):
        self.icon_add_l = http_icon_tuple
        self.http_n = self.icon_add_l[0]
        self.icon_n = self.icon_add_l[1]
        super(SearchButton, self).__init__(self.icon_n, size, an_type, an_time, change_size, change_period)
    def wheelEvent(self, event):
        self.index_n = [i[0] for i in self.icon_add_l].index(self.http_n)
        if event.angleDelta().y() > 0:
            self.index_n += 1
        else:
            self.index_n -= 1
        self.index_n = self.index_n % len(self.icon_add_l)
        self.http_n, self.icon_n = self.icon_add_l[self.index_n]
        self.setIcon(self.icon_n)

class ShortcutEntry(YohoPushButton):
    def __init__(self, parent:QMainWindow, config:Config_Manager):
        self.up = parent
        self.config = config.deepcopy()
        self.name = 'shortcut_entry'
        self.config.group_chose(mode="Launcher", widget=self.name)
        icon_p = self.config.get("icon", obj="path")

        super().__init__(icon_p, int(1.2*self.up.het), "shake")
        self.setParent(parent)

class ShortcutButton(QWidget):
    def __init__(self, parent: QMainWindow, config:Config_Manager) -> None:
        super().__init__(parent)
        self.name = "shortcut_button"
        self.up = parent
        self.config = config.deepcopy().group_chose(mode="Launcher", widget=self.name)
        self.layout_0 = QVBoxLayout()
        self.setLayout(self.layout_0)
        self._initpara()
        self._initUI()
        #self.setFixedSize(*self.config.get(None, widget="Size", obj=self.name)[-2:], )

    def _initpara(self):
        self.v_num = self.config.get('vertical_button_num', mode="Common", widget=None, obj=None)
        self.h_num = self.config.get('horizontal_button_num', mode="Common", widget=None, obj=None)
        self.h_layout = [QHBoxLayout() for _ in range(self.v_num)]
        self.df_path = self.config.get("setting_xlsx", mode="Launcher", widget=self.name, obj='path')
        self.df:pd.DataFrame = excel_to_df(self.df_path,region="A:C")
        self.num_real = self.df.shape[0]
        self.buttonlabel_list = []
        self.num_exp = self.v_num * self.h_num
        self.size_i = self.config.get('shortcut_button_r', mode='Common', widget=None, obj='Size')
        self.font_i = self.config.get('button_title', obj="font")
        self.color_i = self.config.get('button_hover', obj="color")
    def _launch(self, path:str):
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
                if index_f < self.num_real:
                    name, icon, path = self.df.iloc[index_f, 0:3]
                else:
                    name = "Unset"
                    icon = self.config.get('default_button_icon', obj='path')
                    path = os.getcwd()
                layout_i = QVBoxLayout()
                button_i = YohoPushButton(icon, self.size_i, an_type="resize")
                label_i = AutoLabel(name, self.font_i)
                button_i.setStyleSheet(f'''  QPushButton {{
                                            border-radius: 20px; 
                                            background-color: transparent; 
                                            border: 0px solid #BFBFBF; }} 
                                            QPushButton:hover {{ 
                                            background-color: {self.color_i}; }}''')
                button_i.clicked.connect(partial(self._launch, path=path))
                self.buttonlabel_list.append((button_i, label_i))
                layout_i.addWidget(button_i)
                layout_i.addWidget(label_i)
                layout_if.addLayout(layout_i)
                index_f += 1
            self.layout_0.addLayout(layout_if)                    
    
    def refresh(self):
        self.df:pd.DataFrame = excel_to_df(self.df_path,region="A:C")
        index_f = 0
        for v_i in range(self.v_num):
            for h_i in range(self.h_num):
                layout = self.h_layout[v_i]
                if index_f < self.num_real:
                    name, icon, path = self.df.iloc[0:3, index_f]
                else:
                    name = "Unset"
                    icon = self.config.get('default_button_icon', obj='path')
                    path = os.getcwd()
                button_i, label_i = self.buttonlabel_list[index_f]
                button_i.clicked.disconnect()  # cutoff all connections
                button_i.clicked.connect(partial(self._launch, path=path))
                button_i.setIcon(QIcon(icon))
                label_i.setText(name)

class ShortcutSetting(QWidget):
    def __init__(self, parent:QMainWindow, config:Config_Manager):
        super().__init__()
        self.up = parent
        self.name = 'shortcut_setting'
        self.config = config.deepcopy().group_chose(mode="Launcher", widget=self.name)
        self.layout_0 = QVBoxLayout()
        self._windowset()
        self._initpara()
        self._initUI()

    def _windowset(self):
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("Shortcut Setting")

        self.setWindowIcon(QIcon(self.config.get("taskbar_icon", obj="path")))
    
    def _initpara(self):
        # init other para
        self.title_i = self.config.get('window_title', obj='name')
        self.v_num = self.config.get('vertical_button_num', mode="Common", widget=None, obj=None)
        self.h_num = self.config.get('horizontal_button_num', mode="Common", widget=None, obj=None)
        self.num_t = int(self.v_num*self.h_num)
        self.objs = []
        self.option_button = []
        # init font para
        self.config.group_chose(obj='font')
        self.window_title_font = self.config.get('window_title')
        self.coordinate_label_font = self.config.get('coordinate_label')
        self.app_name_label_font = self.config.get('app_name_label')
        self.exe_lineedit_font = self.config.get('exe_lineedit')
        self.option_button_font = self.config.get('option_button')
        
        # init path
        self.config.group_chose(obj='path')
        self.df_path = self.config.get('setting_xlsx')
        self.df = excel_to_df(self.df_path, region="A:C")
        self.taskbar_icon = self.config.get('taskbar_icon')
        self.button_icons = self.config.get('button_icons')
        self.default_app_icon = self.config.get('default_app_icon')
        self.default_folder_icon = self.config.get('default_folder_icon')

        self.col_coordinate_icon = self.config.get('col_coordinate_icon')
        self.col_name_icon = self.config.get('col_name_icon')
        self.col_icon_icon = self.config.get('col_icon_icon')
        self.col_path_icon = self.config.get('col_path_icon')
        self.col_search_icon = self.config.get('col_search_icon')

        # size para
        self.config.group_chose(obj='size')
        for i in range(5):
            setattr(self, f"colwidth_{i}", self.config.get(f"colwidth_{i}"))
        pass
    def _check_path_validity(self, index_f:int):
        line_edit:QLineEdit = self.objs[index_f]['exe_edit']
        text_f = line_edit.text()
        if os.path.exists(text_f) or (not text_f):
            line_edit.setStyleSheet("border: 1px solid grey; background-color: transparent;")  # 路径不存在，变红
        elif os.path.isabs(text_f):
            line_edit.setStyleSheet("border: 3px solid #F0F411; background-color: transparent;")  # 路径不存在，变红
        else:
            line_edit.setStyleSheet("border: 3px solid #EE1515; background-color: transparent;")  # 路径存在，变黄
    
    def _icon_change(self, index_f:int):
        icon_path_ori = self.df.iloc[index_f, 1]
        icon_dir_ori = os.path.basename(icon_path_ori)
        name = self.objs[index_f]['name_edit'].text()
        dir_f = icon_dir_ori if os.path.exists(icon_dir_ori) else ""
        options = QFileDialog.Options()
        file_filter = "SVG Files (*.svg);;ICO Files (*.ico)"
        file_path, _ = QFileDialog.getOpenFileName(self, f"Choose '{name}' icon", dir_f, file_filter, options=options)
        if not file_path:
            return
        _, format_f = os.path.splitext(file_path)
        
        icon_dir = self.config.get("button_icons_dir", mode="Launcher", widget="shortcut_setting", obj="path")
        dst = os.path.join(icon_dir, name+format_f)
        if os.path.exists(icon_path_ori):
            os.remove(icon_path_ori)
        if os.path.exit(dst):
            os.remove(dst)
        shutil.copy2(file_path, dst)
        self.df.iloc[index_f, 1] = dst
        self.objs[index_f]['icon_button'].setIcon(QIcon(dst))

    def _exe_search(self, index_f:int):
        exe_path_ori = self.df.iloc[index_f, 2]
        exe_dir_ori = os.path.basename(exe_path_ori)
        name = self.objs[index_f]['name_edit'].text()
        dir_f = exe_dir_ori if os.path.exists(exe_dir_ori) else ""
        options = QFileDialog.Options()
        file_filter = "All Files (*);;Folders"
        file_path, _ = QFileDialog.getOpenFileName(self, f"Choose '{name}' launch file", dir_f, file_filter, options=options)
        if file_path:
            self.objs[index_f]['exe_edit'].setText(path_format(file_path))
    
    def _read_data(self):
        for i in range(self.num_t):
            name = self.objs[i]['name_edit'].text()
            exe_path = self.objs[i]['exe_edit'].text()
            if is_path(exe_path, exist_check=True):
                self.df[i][2] = exe_path
            self.df[i][0] = name
    
    def _confirm_action(self, sign_f:Literal[True, False, "launcher", "shortcut"]):
        match sign_f:
            case "launcher":
                self.up.launch("launcher")
                return
            case "shortcut":
                self.up.launch("shortcut")
                return 
            case False:
                self.close()
                return
            case True:
                pass
            case _:
                warnings.warn(f"ShorcutSetting._confirm_action recive illegal para {sign_f}")
                return
        
        self.up.reload_shortcutbutton()
        self.hide()
        self._read_data()
        # write in dataframe
        wb = openpyxl.load_workbook(self.up.path_set['Shortcut Setting']['shortcut_set'], data_only=True)
        ws = wb.worksheets[0]
        for row_i in range(self.num_t):
            for col_i in range(3):
                ws.cell(row=row_i+2, column=col_i+1, value=self.df.iloc[row_i, col_i])
        wb.save(self.df_path)
        self.close()
    

    ## UI set
    def _initUI(self):
        up_geom = self.up.geometry()
        x, y, w, h = up_geom.x(), up_geom.y(), up_geom.width(), up_geom.height()
        x_1, y_1, w_1, h_1 = self.config.get(self.name, widget=None, obj="Size")
        self.setGeometry(x+w//2-w_1//2, y+h//2-h_1//2, w_1, h_1)
        
        self._init_title()
        self._init_colname()
        self._init_obj()
        #self._init_action_button()
        self.setLayout(self.layout_0)

    def _init_title(self):
        title_label = AutoLabel(self.title_i, self.window_title_font)
        title_label.setFixedHeight(int(1.5*self.up.het))  # 指定标题高度
        title_label.setAlignment(Qt.AlignCenter)
        self.layout_0.addWidget(title_label)
    
    def _init_colname(self):
        self.layout_col = QHBoxLayout()
        self.config.group_chose(obj="name")

        col_names_size = {'coordinate':self.colwidth_0, 
                          'name':self.colwidth_1, 
                          'icon':self.colwidth_2, 
                          'path':self.colwidth_3, 
                          'search':self.colwidth_4}
        for name_i, size_i in col_names_size.items():
            col_label = QLabel()
            icon_f = getattr(self, f"col_{name_i}_icon")
            col_label.setPixmap(QIcon(icon_f).pixmap(self.up.het, self.up.het))  # 设置图标的大小  
            col_label.setFixedSize(*size_i)  
            col_label.setStyleSheet("background-color: transparent;")  # 设置标题透明背景
            col_label.setAlignment(Qt.AlignCenter)
            self.layout_col.addWidget(col_label)
        
        # layout_widget = QWidget()
        # layout_widget.setLayout(self.layout_col)
        # layout_widget.setFixedWidth(int(0.96*self.w_1))  # 设置布局的宽度为300像素
        # self.layout_0.addWidget(layout_widget)
        self.layout_0.addLayout(self.layout_col)
    
    def _get_obj(self, index:int):
        if index < self.df.shape[0]:
            name_if = self.df.iloc[index, 0]
            icon_if = self.df.iloc[index, 1] if is_path(self.df.iloc[index, 1], True) else self.default_app_icon
            exe_f = self.df.iloc[index, 2]
        else:
            name_if = 'Uncertain'
            icon_if = self.default_app_icon
            exe_f = os.getcwd()
        output = []
        # coordinate define
        coordinate_name = f"{(index+1)%self.h_num}, {(index+1)//self.h_num+1}"
        
        cor_label = AutoLabel(coordinate_name, self.coordinate_label_font)
        cor_label.setStyleSheet('''background-color: transparent;
                                        border:none''')  # 设置标题透明背景
        output.append(cor_label)

        
        name_if = name_if if isinstance(name_if, str) else 'Uncertain'
        name_edit = QLineEdit(name_if)
        name_edit.setFixedSize(*self.colwidth_1)
        name_edit.setFont(self.app_name_label_font)
        name_edit.setStyleSheet("background-color: transparent;")
        output.append(name_edit)

        
        icon_button = YohoPushButton(icon_if, self.up.het, an_type='resize', an_time="resize")
        icon_button.setFixedSize(*self.colwidth_2)
        icon_button.setStyleSheet('''QPushButton {
                                    background-color: transparent;
                                    border: none;
                                    padding: 10px 20px;
                                    }
                                    QPushButton:pressed {
                                        padding: 8px 18px;
                                    }
                                    ''')
        output.append(icon_button)
        
        
        exe_edit = QLineEdit()
        exe_edit.setFixedSize(*self.colwidth_3)
        exe_edit.setPlaceholderText(exe_f)
        exe_edit.setFont(self.exe_lineedit_font)
        exe_edit.setStyleSheet("background-color: transparent;")
        output.append(exe_edit)
        

        folder_button = YohoPushButton(self.default_folder_icon, self.colwidth_4[1], an_type='resize')
        folder_button.setFixedSize(*self.colwidth_4)
        folder_button.setStyleSheet("background-color: transparent;border:none")
        output.append(folder_button)
        return output

    def _init_obj(self):
        obj_layout = QVBoxLayout()
        num_t = int(self.v_num*self.h_num)
        for i_f in range(num_t):
            layout_h = QHBoxLayout()
            col_label, name_edit, icon_button, exe_edit, folder_button = self._get_obj(i_f)
            self.objs.append({"index":i_f, "col_label":col_label, "name_edit":name_edit, 
                              "icon_button":icon_button, "exe_edit":exe_edit, "folder_button":folder_button})
            icon_button.clicked.connect(partial(self._icon_change, index_f=i_f))
            exe_edit.textChanged.connect(partial(self._check_path_validity, index_f=i_f))
            folder_button.clicked.connect(partial(self._exe_search, index_f=i_f))
            for i in [col_label, name_edit, icon_button, exe_edit, folder_button]:
                layout_h.addWidget(i)
            obj_layout.addLayout(layout_h)

        # Create a scroll area and add the content layout to it
        scroll_content = QWidget()  # Create a widget to contain the layout
        scroll_content.setLayout(obj_layout)
        
        frame = QFrame()  # Create a frame to contain the scroll area
        frame_layout = QVBoxLayout()
        frame_layout.addWidget(scroll_content)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame.setLayout(frame_layout)
        frame.setStyleSheet("background: transparent;border-radius: 10px; border: 1px solid gray; background-color: transparent;")  # Set border to the frame
        
        scroll_area = QScrollArea()
        scroll_area.setWidget(frame)  # Set the frame as the widget of the scroll area
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("background: transparent; border: none;")  # Set background to transparent and no border to the scroll area
        self.layout_0.addWidget(scroll_area)
        
        # Customize scrollbar style
        scroll_bar = scroll_area.verticalScrollBar()
        scroll_bar.setStyleSheet("""
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 20px;
                margin: 5px;
                
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 25);
                min-height: 20px;
                border-radius: 5px;
            }

            QScrollBar::handle:vertical:hover {
                background: #737373;
            }
            QScrollBar::add-line:vertical {
                background: transparent;
                height: 0px;
                subcontrol-position: bottom;
                subcontrol-origin: margin;
            }
            QScrollBar::sub-line:vertical {
                background: transparent;
                height: 0px;
                subcontrol-position: top;
                subcontrol-origin: margin;
            }
            QScrollBar::sub-page:vertical, QScrollBar::add-page:vertical {
            background: transparent; 
            }
        """)

    def _init_action_button(self):
        button_layout = QHBoxLayout()
        self.config.group_chose("Launcher", "shortcut_setting", "color")
        launcher_button = ColorfulButton("Launcher",
                                         self.option_button_font, 
                                         self.config['launcher0'],
                                         self.config['launcher1'],
                                         self.config['launcher2'],)
        launcher_button.clicked.connect(self._confirm_action)
        shortcut_button = ColorfulButton("Shortcut",
                                         self.option_button_font, 
                                         self.config['shortcut0'],
                                         self.config['shortcut1'],
                                         self.config['shortcut2'])
        shortcut_button.clicked.connect(self._confirm_action)
        confirm_button = ColorfulButton("Confirm", 
                                        self.option_button_font, 
                                        self.config['confirm0'],
                                        self.config['confirm1'],
                                        self.config['confirm2'],
                                        )
        confirm_button.clicked.connect(self._confirm_action)

        cancel_button = ColorfulButton("Cancel",
                                       self.option_button_font,
                                       self.config['cancel0'],
                                       self.config['cancel1'],
                                       self.config['cancel2'],)
        cancel_button.clicked.connect(self._confirm_action)

        self.option_button.extend([launcher_button, shortcut_button, confirm_button, cancel_button])
        button_layout.addWidget(launcher_button)
        button_layout.addWidget(shortcut_button)
        button_layout.addWidget(confirm_button)
        button_layout.addWidget(cancel_button)
        self.layout_0.addLayout(button_layout)

class Terminal(QTextEdit):
    def __init__(self, config:Config_Manager, parent:QMainWindow):
        super().__init__(parent)
        self.name = 'Terminal'
        self.config=config.deepcopy()
        self.config.group_chose(mode='Terminal', widget=None)
        self._setstyle()
    def _setstyle(self):
        self.setReadOnly(True)
        self.setFont(self.config.get('main', obj="font"))
        
        self.main_style_sheet = f'''
            QTextEdit {{
                color: {self.config.get('text', obj='color')};
                background-color: {self.config.get('background', obj='color')};
                border: 0px solid #1E1F22;
                border-radius: 20px}}
        '''
        self.setStyleSheet(self.main_style_sheet)
        self.bar_style = f'''
        QScrollBar:vertical {{
            background: transparent;
            width: 10px;
            margin: 0px;
        }}

        QScrollBar::handle:vertical {{
            background: {self.config.get('scroll_bar', obj='color')} ;
            min-height: 20px;
            border-radius: 5px;
        }}

        QScrollBar::sub-line:vertical,
        QScrollBar::add-line:vertical,
        QScrollBar::sub-page:vertical,
        QScrollBar::add-page:vertical {{
            background: none;
            }}
        '''
        self.verticalScrollBar().setStyleSheet(self.bar_style)
    
    def add_text(self, text_f:str, color:str):
        pass
    
    def add_command(self, text_f:str):
        pass
    
    def add_error(self, text_f:str):
        pass

class TransferProgress(ProgressBar):
    def __init__(self, parent, max_value, height):
        self.up = parent
        super().__init__(parent, max_value, height)

class ExePathLine(QLineEdit):
    def __init__(self, height_f:int, 
                 place_holder:str,
                 font:QFont,
                 colors:List[str] = ["#F7F7F7", "#F0F411","#EE1515"]):
        # super().__init__(height_f, scrollbar_color, scrollbar_color_hover, scrollbar_color_pressed)
        super().__init__()
        self.background_color, self.warning_color, self.error_color = colors
        self.setMaximumHeight(height_f)
        self.setPlaceholderText(place_holder)
        self.font_f = font
        self._setstyle()
        self.textChanged.connect(self._text_change)
    
    def _setstyle(self):
        self.setFont(self.font_f)
        self.setToolTip("sadasdad"+self.text())  # 鼠标悬停时显示完整文本
        self.style_sheet = f'''
        QLineEdit{{
        background-color: {self.background_color};  
        border-radius: 10px;
        }}
        QToolTip {{
        background-color: {self.background_color};  
        color: #161616;           
        font-family:: Consolas;
        font-size: 40px;         
        border-radius: 6px;      
        padding: 8px;            
        }}
        '''
        self.setStyleSheet(self.style_sheet)

    def _text_change(self, text):
        self.setToolTip(text)
        if os.path.exists(text) or (not text):
            color_n = self.background_color
        elif os.path.isabs(text):
            color_n = self.warning_color
        else:
            color_n = self.error_color
        self.style_sheet = f'''
        QLineEdit{{
        background-color: {color_n};  
        border-radius: 10px;
        }}
        QToolTip {{
        background-color: {self.background_color};  
        color: #161616;           
        font-family:: Consolas;
        font-size: 40px;         
        border-radius: 6px;      
        padding: 8px;            
        }}
        '''
        self.setStyleSheet(self.style_sheet)

class NameEdit(QLineEdit):
    def __init__(self, text_f:str, font:QFont, height:int,
                 background_f:str="#F7F7F7",):
        super().__init__()
        self.setText(text_f)
        self.setFont(font)
        self.setFixedHeight(height)
        style_sheet = f'''
            QLineEdit {{
                background-color: {background_f};  
                border: none; 
                border-radius: 10px;        
                padding: 10px;              
            }}
        '''
        self.setStyleSheet(style_sheet)

class SheetControl(QTabBar):
    def __init__(self, parent:QWidget, color_l:List[str], icon_l:List[str], height:int):
        super().__init__(parent)
        self.up = parent
        self._stestyle(color_l, icon_l, height)
        self.setFont(QFont("Consolas", 8))
        self.setElideMode(Qt.ElideNone)
    
    def wheelEvent(self, event):
        event.ignore()
    
    def _stestyle(self, color_l:List[str], icon_l:List[str], height_f:int):
        icon_l = [i.replace('\\', '/') for i in icon_l]
        style_sheet = f"""
        QTabBar{{
            border: none;
            background: transparent; 
        }}
        QTabBar::tab {{
            margin-right: 10px;
            padding: 5px 10px;
            border-radius: 10px;
            height: {height_f}px;  /* 设置标签高度 */
            background: {color_l[0]};
        }}
        QTabBar::tab:selected {{
            background: {color_l[2]};
        }}
        QTabBar::tab:hover {{
            background: {color_l[1]};
        }}
        QTabBar::tab:!selected {{
        }}
        QTabBar::close-button {{
        image: url("{icon_l[0]}"); 
        subcontrol-position: right; 
        margin: 2px; 
        }}
        """
        #self.setTabsClosable(True)
        self.setMovable(True) 
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_context_menu)
        self.setStyleSheet(style_sheet)

    def get_texts(self):
        texts = []
        for index in range(self.count()):  
            texts.append(self.tabText(index))  
        return texts
    
    def get_current_text(self):
        index = self.currentIndex()
        return self.tabText(index)
    
    def set_current_tab(self, name:str):
        if name in self.get_texts():
            index = self.get_texts().index(name)
            self.setCurrentIndex(index)

    def open_context_menu(self, position): 
        index = self.tabAt(position)
        if index == -1:
            return
        menu = QMenu()
        rename_action = menu.addAction("Rename")
        close_action = menu.addAction("Delete")

        action = menu.exec_(self.mapToGlobal(position))
        if action == rename_action:
            self.up.rename_tab(index)
        elif action == close_action:
            self.up.close_tab(index)


class LauncherSetting(QWidget):
    def __init__(self, config:Config_Manager, parent:QMainWindow, manager:LauncherPathManager):
        super().__init__(parent)
        self.up = parent
        self.manager = manager
        self.config = config.deepcopy()
        self.name = 'LauncherSetting'
        self.config.group_chose(mode='Settings', widget=self.name)
        self._layout_set()
        self._load()
        self._layout_load()
    
    def _layout_set(self):
        self.layout_0 = amlayoutV(align_h='c', spacing=5)
        self.setLayout(self.layout_0)
        self.objs = {'icon':[], 'name':[], "chname":[], 'exe':[], 'search':[]}
    
    def _layout_load(self):
        self._init_tiles()
        self._init_layout()
        self._init_multi_line()
        self._init_add_line()
        self._bottom_control()
        add_obj(self.add_button_lo, parent_f=self.obj_layout)
        self.obj_layout.addStretch()
        add_obj(self.title_layout, self.scroll_area,parent_f=self.layout_0)
        self.layout_0.addLayout(self.bottom_layout)
        self._line_fresh(0)
    
    def _load(self):
        self.df = self.manager.df
        self.dfc = self.df.copy(deep=True)
        self.dfc['IconID'] = None
        self.tmp_icon_folder = self.config.get('tmp_icon_folder', obj='path')
        self.default_app_icon = self.config.get('default_button_icon', 'Launcher', 'shortcut_button', 'path')
        self.name_font = self.config.get('name', obj='font')
        self.chname_font = self.config.get('chname', obj='font')
        self.exe_font = self.config.get('exe', obj='font')
        self.line_height = self.config.get('line_height', obj='Size')
        self.searcher_icon = QIcon(self.config.get('searcher_icon', obj='path'))
        self.add_button_margin = self.config.get('add_button_margin', obj='Size')
        self.col_margin = self.config.get('col_margin', obj='Size')
        self.num = int(self.config.get('ori_line_num', obj=None))
        self.nameedit_length = self.config.get('namedit_max_length', obj='Size')
        self.nameedit_color = self.config.get('nameedit_background', obj='color')
        self.exeedit_min_length = self.config.get('exeedit_min_ledngth', obj='Size')
        self.exeedit_color = self.config.get('exeedit_background', obj='color')
        self.tab_height = self.config.get('tab_height', obj='Size')
        self.bottom_margin = self.config.get('bottom_margin', obj='Size')
        self.line_num = 0
        self.objs_l = {}
        self.widget_l = []
    
    def _init_tiles(self):
        self.title_layout = amlayoutH()
        self.title_layout.setContentsMargins(self.col_margin[0], 0, self.col_margin[1], 0)
        self.titles = ['number_col', 'icon_col', 'name_col', 'chname_col','exe_col', 'searcher']
        width_l = [self.line_height, self.line_height, self.nameedit_length, self.nameedit_length, self.exeedit_min_length, self.line_height]
        for i, title_i in enumerate(self.titles):
            col_i = QLabel(self)
            col_style_sheet = f'''
            background: {self.config.get('col_background', obj='color')};
            text_align
            '''
            col_i.setStyleSheet(col_style_sheet)
            icon_i = QPixmap(self.config.get(f'{title_i}_icon',obj='path'))
            # size_i = self.config.get('col_icon_size', obj='Size')
            col_i.setPixmap(icon_i.scaled(QSize(self.line_height, self.line_height)))
            if self.titles[i] != 'exe_col':
                col_i.setFixedWidth(width_l[i])
            col_i.setAlignment(Qt.AlignCenter)
            setattr(self, title_i, col_i)
            self.title_layout.addWidget(getattr(self, title_i))

    def _init_layout(self):
        self.obj_layout = amlayoutV(spacing=self.config.get('line_spacing', obj='Size'))
        # Create a scroll area and add the content layout to it
        self.scroll_content = QWidget()  # Create a widget to contain the layout
        self.scroll_content.setLayout(self.obj_layout)
        self.frame = QFrame()  # Create a frame to contain the scroll area
        self.frame_layout = QVBoxLayout()
        self.frame_layout.addWidget(self.scroll_content)
        self.frame_layout.setContentsMargins(0, 0, 0, 0)
        self.frame.setLayout(self.frame_layout)
        self.frame.setObjectName("OuterFrame")
        self.frame.setStyleSheet("""
                        QFrame#OuterFrame {
                            background: transparent;
                            border-radius: 10px;
                            border: 1px solid gray;
                            background-color: transparent;
                        }
                    """)  # Set border to the frame
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("myScrollArea")
        self.scroll_area.setWidget(self.frame)  # Set the frame as the widget of the scroll area
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
                        QScrollArea#myScrollArea {
                            background: transparent;
                            border: none;
                        }
                    """)  # Set background to transparent and no border to the scroll area
        
        # Customize scrollbar style
        self.scroll_bar = self.scroll_area.verticalScrollBar()
        self.scroll_bar.setStyleSheet("""
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 20px;
                margin: 5px;
                
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 25);
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #737373;
            }
            QScrollBar::add-line:vertical {
                background: transparent;
                height: 0px;
                subcontrol-position: bottom;
                subcontrol-origin: margin;
            }
            QScrollBar::sub-line:vertical {
                background: transparent;
                height: 0px;
                subcontrol-position: top;
                subcontrol-origin: margin;
            }
            QScrollBar::sub-page:vertical, QScrollBar::add-page:vertical {
            background: transparent; 
            }
        """)

    def _init_single_line(self, index_f:int, df:pandas.DataFrame=None, default:bool=False, insert:bool=False):
        if default is not False:
            icon_i = QIcon(self.default_app_icon)
            name = ''
            chname = ''
            exe_path = ''
        else:
            name = df.iloc[index_f, 0]
            icon_i = self.manager.get_icon(name)
            chname = df.iloc[index_f, 1]
            exe_path = df.iloc[index_f, 3]
            if os.path.isfile(exe_path):
                exe_path = os.path.basename(exe_path)
        index_i = len(self.objs_l.keys())
        nummber_w = QLabel(str(index_i))
        nummber_w.setFont(self.config.get('number', obj='font'))
        nummber_w.setAlignment(Qt.AlignCenter)
        nummber_w.setStyleSheet("background-color: transparent; border: none;text-align: center;")
        nummber_w.setFixedWidth(self.line_height)
        nummber_w.setFixedHeight(self.line_height)
        icon_w = YohoPushButton(icon_i, self.line_height, 'shake')
        icon_w.setProperty('index', index_i)
        icon_w.clicked.connect(lambda: self._change_icon(index_i))
        name_label = NameEdit(name, self.name_font, self.line_height, self.nameedit_color)
        name_label.setMaximumWidth(self.nameedit_length)
        chname_label = NameEdit(chname, self.chname_font, self.line_height, self.nameedit_color)
        chname_label.setMaximumWidth(self.nameedit_length)
        exe_edit = ExePathLine(self.line_height,exe_path,self.exe_font,self.exeedit_color)
        exe_edit.setMinimumWidth(self.exeedit_min_length)
        exe_edit.textChanged.connect(self._edit_change)
        folder_button = YohoPushButton(self.searcher_icon, self.line_height, an_type='resize')
        folder_button.clicked.connect(lambda: self._exe_search(index_f))
        self.objs_l[len(self.objs_l.keys())] = {'number':nummber_w, 'icon':icon_w, 'name':name_label, 'chname':chname_label, 'exe':exe_edit, 'search':folder_button}
        layout_i = amlayoutH()
        layout_i.setMargin(0)
        setattr(self, f'widget_{len(self.objs_l.keys())}', QWidget())
        widget_i = getattr(self, f'widget_{len(self.objs_l.keys())}')
        widget_i.setLayout(layout_i)
        add_obj(nummber_w, icon_w, name_label, chname_label, exe_edit, folder_button, parent_f=layout_i)
        self.widget_l.append(widget_i)
        if insert:
            self.obj_layout.insertWidget(self.obj_layout.count()-1, widget_i)
        else:
            self.obj_layout.addWidget(widget_i)
        #return nummber_w, icon_w, name_label, chname_label, exe_edit, folder_button
    
    def _init_multi_line(self):
        for i in range(self.num):
            self._init_single_line(i, default=True)
            #nummber_w, icon_w, name_label, chname_label, exe_edit, folder_button = self._init_single_line(i, default=True)
            # self.objs_l[i] = {'number':nummber_w, 'icon':icon_w, 'name':name_label, 'chname':chname_label, 'exe':exe_edit, 'search':folder_button}
            # layout_i = amlayoutH()
            # layout_i.setMargin(0)
            # widget_i = QWidget()
            # widget_i.setLayout(layout_i)
            # add_obj(nummber_w, icon_w, name_label, chname_label, exe_edit, folder_button, parent_f=layout_i)
            # self.obj_layout.addWidget(widget_i)
            # self.widget_l.append(widget_i)

    def _init_add_line(self):
        color_l = self.config.get('add_button', obj='color')
        self.add_style_sheet = f'''
            QPushButton {{
                border: none;
                border-radius: 10px;
                background-color: {color_l[0]};
                text-align: center; 
            }}
            QPushButton:hover {{
                background-color: {color_l[1]};  
            }}
            QPushButton:pressed {{
                background-color: {color_l[2]};                   
            }}
        '''
        self.add_button = YohoPushButton(QIcon(self.config.get('add_button_icon',obj='path')), self.line_height, an_type='resize', style_assign=self.add_style_sheet)
        # self.add_button = QPushButton()
        # self.add_button.setIcon(QIcon(self.config.get('add_button_icon',obj='path')))
        self.add_button.setIconSize(QSize(self.line_height, self.line_height))
        self.add_button.setFixedHeight(self.config.get('add_line_height', obj='Size'))
        self.add_button.setMaximumWidth(11111)
        self.add_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.add_button.clicked.connect(self._insert_line)
        self.add_button_lo = amlayoutH()
        self.add_button_lo.setContentsMargins(self.add_button_margin[0], 0, self.add_button_margin[1], 0)
        add_obj(self.add_button, parent_f=self.add_button_lo)
    
    def _line_fresh(self, index_f:int):
        name_f = self.tab_bar.tabText(index_f)
        self.line_num = 0
        #name_f = self.tab_bar.get_current_text()
        if name_f not in set(self.dfc.loc[:,'Group'].tolist()):
            self.widget_l[0].setVisible(True)
            self.objs_l[0]['number'].setText('0')
            self.objs_l[0]['name'].setText('')
            self.objs_l[0]['chname'].setText('')
            self.objs_l[0]['exe'].setText('')
            self.objs_l[0]['icon'].setIcon(QIcon(self.default_app_icon))
            for i in range(1, self.num):
                self.widget_l[i].setVisible(False)
            self.line_num += 1
            return
        df_n = self.dfc[self.df['Group']==name_f]
        for i in range(df_n.shape[0]):
            if i >= self.num:
                self._insert_line()
            self.widget_l[i].setVisible(True)
            self.objs_l[i]['number'].setText(str(i))
            self.objs_l[i]['name'].setText(df_n.iloc[i, 0])
            self.objs_l[i]['chname'].setText(df_n.iloc[i, 1])
            self.objs_l[i]['exe'].setText(df_n.iloc[i, 3])
            icon_c = df_n.iloc[i,-1]
            if False:
                self.objs_l[i]['icon'].setIcon(QIcon(df_n.iloc[i, -1]))
            else:
                icon_d = self.manager.get_icon(df_n.iloc[i, 0])
                self.objs_l[i]['icon'].setIcon(icon_d)
            self.line_num += 1
        for i in range(len(self.widget_l)):
            if i >= df_n.shape[0]:
                self.widget_l[i].setVisible(False)
    
    def _bottom_control(self):
        self.bottom_layout = amlayoutH('c', spacing=25)
        self.tab_wdiget = QWidget()
        self.tab_layout = amlayoutH('l', spacing=10)
        self.tab_wdiget.setLayout(self.tab_layout)
        tab_color = self.config.get('tab_button', obj='color')
        tab_delete_icon = self.config.get('tab_delete', obj='path')
        self.tab_bar = SheetControl(self, tab_color, tab_delete_icon, int(0.8*self.tab_height))
        
        for name_i in set(self.dfc.loc[:, 'Group'].to_list()):
            self.tab_bar.addTab(name_i)
        self.tab_bar.currentChanged.connect(self._line_fresh)
        self.tab_bar.setCurrentIndex(0)
        self.tab_bar.setFixedHeight(self.tab_height)
        self.b_add_button = YohoPushButton(QIcon(self.config.get('add_sheet_button', obj='path')), self.line_height, an_type='resize')
        self.b_add_button.clicked.connect(self.add_tab)
        self.tab_layout.addWidget(self.tab_bar)
        add_obj(self.b_add_button, parent_f=self.tab_layout)
        
        self.save_button = ColorfulButton('Save', self.config.get('save_button', obj='color'), self.config.get('save_button', obj='font'), self.line_height)
        self.save_button.clicked.connect(self._save)
        self.reset_button = ColorfulButton('Reset', self.config.get('reset_button', obj='color'), self.config.get('set_button', obj='font'), self.line_height)
        self.reset_button.clicked.connect(self._reset)
        # self.discard_button = ChangeControl('Discard', self.config.get('discard_button', obj='color'), self.config.get('discard_button', obj='font'), self.line_height)
        # self.discard_button.clicked.connect(self._discard)
        self.bottom_layout.setContentsMargins(self.bottom_margin[0], 0, self.bottom_margin[1], 0)
        self.bottom_layout.addWidget(self.tab_wdiget)
        self.bottom_layout.addStretch()
        add_obj(self.save_button, self.reset_button, parent_f=self.bottom_layout)
        
    def _insert_line(self):
        if self.line_num >= len(self.widget_l):
            self._init_single_line(self.line_num, default=True, insert=True)
        else:
            self.widget_l[self.line_num].setVisible(True)
        self.line_num += 1
    
    def add_tab(self, name='new_sheet', refresh:bool=True):
        text_l = self.tab_bar.get_texts()
        for i in range(99):
            name_t = f'{name}_{i}'
            if name_t not in text_l:
                break
        self.tab_bar.addTab(name_t)
        if refresh:
            self._line_fresh(self.tab_bar.count()-1)
    
    def rename_tab(self, index):
        current_name = self.tab_bar.tabText(index)
        new_name, ok = QInputDialog.getText(self, "Rename Sheet", "Enter New Name:", text=current_name)
        if ok and new_name.strip():
            self.tab_bar.setTabText(index, new_name)
        self.dfc['Group'] = self.dfc['Group'].replace(current_name, new_name)
    
    def close_tab(self, index):
        tip_prompt = f'Are you sure to DELETE sheet "{self.tab_bar.tabText(index)}"?'
        out_f = self.up.tip('Warning', tip_prompt, {'Yes':True, 'No':False}, False)
        if out_f:
            self.tab_bar.removeTab(index)
            self.dfc = self.dfc[self.dfc['Group']!=self.tab_bar.tabText(index)]
    
    def _change_icon(self, index_f:int):
        file_filter = "Images (*.svg *.png *.jpg *.jpeg *.ico)"
        file_path, _ = QFileDialog.getOpenFileName(self, "Select an image", "", file_filter)
        if not file_path:
            return
        icon_i = QIcon(file_path)
        self.objs_l[index_f]['icon'].setIcon(icon_i)
        _, ext = os.path.splitext(file_path)
        id_l = self.dfc.loc[:,'IconID'].to_list()
        name = self.objs_l[index_f]['name'].text()
        id_ls = [i.split('.')[0] for i in id_l if i]
        if name in id_ls:
            for path_i in glob(os.path.join(self.tmp_icon_folder, f'{name}.*')):
                os.remove(path_i)
        
        self.dfc.loc[index_f, 'IconID'] = f'{name}{ext}'
        dst = os.path.join(self.tmp_icon_folder, f'{name}{ext}')
        shutil.copy(file_path, dst)
    
    def _edit_change(self):
        pass

    def _exe_search(self, index_f:int):
        pass
    
    def _reset(self):
        pass

    def _discard(self):
        pass

    def _save(self):
        pass

class InfoTip(QDialog):
    def __init__(self, parent,
                 type_f:Literal['Info', 'Warning', 'Error'], 
                 prompt_f:str, 
                 buttons:OrderedDict[str,Union[str, Dict[Literal['colors', 'value',], Union[bool, str, List[str]]]]],
                 config:Config_Manager=None,):
        super().__init__()
        self.VALUE = -10
        if config and not hasattr(self, 'config'):
            self._load_config(config)
        self.config.group_chose(mode='MainWindow', widget='Tip')
        self.type = type_f
        self.prompt = prompt_f
        self.buttons = buttons
        self._load()
        self._init_ui()
        self._setStyle()
    
    @classmethod
    def _load_config(cls, config:Config_Manager):
        cls.config = config.deepcopy()
    
    def _load(self):
        self.button_margin = self.config.get('button_margin', obj='Size')
        self.prompt_margin = self.config.get('prompt_margin', obj='Size')
        self.title_icon_i = QIcon(self.config.get(f'{self.type}_icon', obj='path'))
        self.title_height = self.config.get('title_height', obj='Size')
        self.title_font = self.config.get('title', obj='font')
        self.prompt_font = self.config.get('prompt', obj='font')
        self.button_font = self.config.get('button', obj='font')
        self.button_size = self.config.get('button_size', obj='Size')
        self.button_colors = self.config.get('button', obj='color')
        self.widget_size = self.config.get('widget_size', obj='Size')
    
    def _init_ui(self):
        self.layout0 = amlayoutV()
        self.setLayout(self.layout0)
        self.layout_tile = amlayoutH(spacing=15)
        self.layout_prompt = amlayoutH()
        self.layout_prompt.setContentsMargins(self.prompt_margin[0], 0, self.prompt_margin[1], 0)
        self.layout_button = amlayoutH()
        self.layout_button.setContentsMargins(self.button_margin[0], 0, self.button_margin[1], 0)
        self.setFont(self.title_font)
        
        self.title_icon = QLabel()
        self.title_icon.setPixmap(self.title_icon_i.pixmap(self.title_height, self.title_height))
        self.title_icon.setFixedSize(self.title_height, self.title_height)
        self.title_icon.setAlignment(Qt.AlignCenter)

        self.title_name = QLabel(self.type)
        self.title_name.setFont(self.title_font)
        self.title_name.setAlignment(Qt.AlignLeft)
        add_obj(self.title_icon, self.title_name, parent_f=self.layout_tile)
        
        self.promt_label = QLabel(self.prompt)
        self.promt_label.setFont(self.prompt_font)
        self.promt_label.setWordWrap(True)
        self.promt_label.setAlignment(Qt.AlignCenter)
        self.layout_prompt.addWidget(self.promt_label)

        for name, value in self.buttons.items():
            button_i  = ColorfulButton(name, self.button_colors, self.font(), self.button_size[-1])
            button_i.setProperty('value', value)
            button_i.setFixedSize(QSize(*self.button_size))
            self.layout_button.addWidget(button_i)
            button_i.clicked.connect(self._return)
        
        add_obj(self.layout_tile, self.layout_prompt, self.layout_button, parent_f=self.layout0)
        self.setFixedSize(QSize(*self.widget_size))
    
    def _setStyle(self):
        style_sheet = f'''
            QWidget {{
                background-color: {self.config.get('background', obj='color')};
                border-radius: 10px;
            }}
        '''
        self.setStyleSheet(style_sheet)
    
    def _return(self):
        button = self.sender()
        self.VALUE = button.property('value')
        super().accept()

