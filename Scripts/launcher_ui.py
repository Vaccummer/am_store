# words match method
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

class Associate:
    def __init__(self, nums:Config_Manager, 
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
            return os.listdir(prompt_f)
        # prompt is a unfilled diretory
        sup_path = path_f.parent
        dir_name_n = path_f.name
        if not sup_path.exists():
            return []
        else:
            list_1f = sorted([dir_if for dir_if in os.listdir(sup_path) if dir_name_n in dir_if], key=lambda x:x.index(dir_name_n))
            list_2f = sorted([dir_if for dir_if in os.listdir(sup_path) if dir_name_n.lower() in dir_if.lower()], key=lambda x:(x.lower()).index(dir_name_n.lower()))
            return rm_dp_list_elem(list_1f+list_2f, reverse=False)
    
    # To associate a programme name of prompt
    def name(self, prompt_f):
        if not prompt_f:
            return []
        output_name = sorted([name_i for name_i in self.names if prompt_f.lower() in name_i.lower()], key=lambda s: (s.lower().index(prompt_f.lower()))/len(s))
        output_chname = sorted([ch_name_i for ch_name_i in self.ch_names if prompt_f.lower() in ch_name_i.lower()], key=lambda s: (s.lower().index(prompt_f.lower()))/len(s))
        output_des = [self.names[self.description.index(dsp_name_i)] for dsp_name_i in self.description if prompt_f.lower() in dsp_name_i.lower()]
        output_chname_t = [i for i in output_chname if self.names[self.ch_names.index(i)] not in output_name]
        output_des_t = [i for i in output_des if self.ch_names[self.names.index(i)] not in output_chname]
        return rm_dp_list_elem(output_name+output_chname_t+output_des_t, reverse=False)[0:self.num]
    
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
    def __init__(self, config:Config_Manager, parent:Union[QMainWindow, QWidget]):  
        super(AssociateList, self).__init__(parent)
        self.up = parent
        self.name = "associate_list"
        self.config = config.deepcopy()
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
        self.launcher_df = LauncherPathManager(self.config).df
        self.ass = Associate(self.num, self.launcher_df)
        self.config.group_chose(mode="Launcher", widget=self.name, obj=None)
        self.download_dir = self.config.get("download_save_dir", obj="path")
        self.max_length = self.config.get("max_length", )
        self.num = self.config.get("max_exe_num", )
        self.max_num = self.config.get("max_dir_num", )
        self.font_a = self.config.get('main', obj='font')
        self.setFont(self.font_a)

        
        self.default_icon = self._load_default_icons()
        self.remote_server:SshManager=None

    def _load_default_icons(self):
        self.default_icon_d = {}
        names_path_d = self.config.get("default_icon", mode="Launcher", widget=None, obj="path")
        for keys, path_i in names_path_d.items():
            if not os.path.exists(path_i):
                continue
            for key_i in keys:
                self.default_icon_d[key_i] = QIcon(path_i)
    
    def _setStyle(self):
        self.setFont(self.config.get("main", obj="font"))
        associate_list_set = tuple(self.config.get(self.name, widget="Size", obj=None))
        self.setGeometry(*associate_list_set)
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
    
    def _get_default_icon(self):
        pass
    
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
        button_i = YohoPushButton(self.ass_icon_default, button_size, an_type="shake")
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
    
    def _geticon(self, name:str):
        if name in self.ass_icon_name:
            return QIcon(self.ass_icon_list[self.ass_icon_name.index(name)])
        else:
            return QIcon(self.ass_icon_default)
    
    def _gettext(self, item:QListWidgetItem):
        index_f = item.data(Qt.UserRole)
        return self.label_l[index_f].text()
    
    def _getbutton(self, item:QListWidgetItem):
        index_f = item.data(Qt.UserRole)
        return self.button_l[index_f]
    
    def left_click(self, item):
        prompt_f = 1
        pass
    
    def right_click(self, pos):
        prompt_f = self.up.inputbos.text() 
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
    
    def _upload(self, src:List[str]):
        pass
    
    def _download(self, item, ask_save_dir:bool):
        if ask_save_dir:
            dir_path = QFileDialog.getExistingDirectory(self, "Choose a directory to save the file")
            if not dir_path:
                return
        else:
            dir_path = self.download_dir
        match self.up.host:
            case "local":
                self._local_download(item, dir_path)
            case _:
                self._remote_download(item, dir_path)
    def _local_download(self, item, dir_path):
        self.up.download_progress_bar
        prompt_f = self.up.input_box.text()
        src = os.path.join(prompt_f, self._gettext(item))
        if os.path.exists(src):
            pass
        else:
            src = os.path.join(os.path.dirname(prompt_f), self._gettext(item))
            if os.path.exists(src):
                pass
            else:
                return
        if os.path.isdir(src):
            files = [src]
        else:
            files = glob(os.path.join(src, "*"), recursive=True)
        
    def _remote_download(self, item, dir_path):
        pass

        pass
    def _cg_default_icon(self, item):
        pass
    
    # to update associate_words
    def update_associated_words(self):
        if self.up.mode != "Launcher":
            return
        current_text:str = self.up.get_input()
        match self.up.host:
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
            matching_words = ['..']+self.ass.path(current_text)
        else:
            if ';' not in current_text:
                matching_words = self.ass.name(current_text)
            else:
                matching_words = self.ass.multi_pro_name(current_text.split(';'))

        for i in range(num_n):
            if i >= len(matching_words):
                self.item_l[i].setHidden(True)
                continue
            text_i = matching_words[i]
            icon_i = self._geticon(text_i, sign_n)
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

class SwitchButton(QComboBox):
    def __init__(self, parent: QMainWindow, config:Config_Manager) -> None:
        super().__init__(parent)
        self.up = parent
        self.name = "switch_button"
        self.config = config.deepcopy()
        self.config.group_chose(mode="MainWindow", widget=self.name)
        self.mode_list = self.config.get("mode_list", mode="Common", widget=None, obj=None)
        self.gem = self.config.get(self.name, widget=None, obj="Size")
        self.currentIndexChanged.connect(self._change_length)  # 连接信号槽
        self._initUI()
    def _initUI(self):
        font_f = self.config.get("font", obj=None)
        self.setFont(font_f)
        for model_if in self.mode_list:
            self.addItem(model_if)
        self.setCurrentIndex(self.mode_list.index(self.up.mode))

        font_metrics = QFontMetrics(self.font())
        w_f = font_metrics.boundingRect(self.up.mode).width() + 30  
        self.setFixedSize(w_f, self.gem[-1])
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
    def _change_length(self):
        mode_n = self.currentText()
        font_metrics = QFontMetrics(self.font())
        w_f = font_metrics.boundingRect(mode_n).width() + 30  
        self.setFixedSize(w_f, self.gem[-1])

class PathModeSwitch(QComboBox):
    def __init__(self, parent:QMainWindow, config:Config_Manager, mode_list:List[str]) -> None:
        super().__init__(parent)
        self.up = parent
        self.name = "path_mode_switch"
        self.config = config.deepcopy()
        self.config.group_chose(mode="Launcher", widget=self.name, obj=None)
        self.setFont(self.config.get("font"))
        self.gem = self.config.get(self.name, widget=None, obj="Size")
        self.currentIndexChanged.connect(self._change_length)
        self.mode_list = mode_list
        self._initUI()
    def _initUI(self):
        font_f = self.config.get("font", obj=None)
        self.setFont(font_f)
        for model_if in self.mode_list:
            self.addItem(model_if)
        self.setCurrentIndex(self.mode_list.index("Local"))
        font_metrics = QFontMetrics(self.font())
        w_f = font_metrics.boundingRect(self.up.mode).width() + 30  
        self.setFixedSize(w_f, self.gem[-1])
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
    def _change_length(self):
        mode_n = self.currentText()
        font_metrics = QFontMetrics(self.font())
        w_f = font_metrics.boundingRect(mode_n).width() + 30  # 加上一些额外空间，你可以根据需要修改
        self.setFixedSize(w_f, self.gem[-1])

class TopButton(QWidget):
    def __init__(self, parent: QMainWindow, config:Config_Manager) -> None:
        super().__init__(parent)
        self.name = "top_button"
        self.up = parent
        self.config = config.deepcopy()
        self.config.group_chose(mode="MainWindow", widget=self.name)
        self.geom = self.config.get(self.name, widget=None, obj="Size")
        self.max_state = False
        self.layout_1 = QHBoxLayout()
        self.layout_1.setAlignment(Qt.AlignRight | Qt.AlignCenter)

        self._initbuttons()
        self.setLayout(self.layout_1)
        self.setFixedSize(QSize(self.geom[-2], self.geom[-1]))
        

    def _initbuttons(self):
        size_i = QSize(self.up.het, self.up.het)
        self.max_path = self.config.get('maximum', obj="path")
        self.min_path = self.config.get('minimum', obj="path")
        self.middle_path = self.config.get('middle', obj="path")
        self.close_path = self.config.get('close', obj="path")

        self.max_button = YohoPushButton(QIcon(self.max_path), size_i, 'resize')
        self.max_button.clicked.connect(self.max_click)
        self.min_button = YohoPushButton(QIcon(self.min_path), size_i, 'resize')
        self.close_button = YohoPushButton(QIcon(self.close_path), size_i, 'resize')
        self.layout_1.addWidget(self.min_button)
        self.layout_1.addWidget(self.max_button)
        self.layout_1.addWidget(self.close_button)

    
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
        self.config.group_chose(mode=self.up.mode, widget="input_box")
        self.setStyleSheet("border-radius: 20px; padding-left: 20px;padding-right: 15px")  # smooth four angle
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

        super().__init__(icon_p, int(1.3*self.up.het), "resize")
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
        self.setFixedSize(*self.config.get(None, widget="Size", obj=self.name)[-2:], )

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
        self._init_action_button()
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








    



    


