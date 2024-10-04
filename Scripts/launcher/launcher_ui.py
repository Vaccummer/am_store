# words match method
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from Scripts.tools.toolbox import *
from PySide2.QtWidgets import QListWidget, QMainWindow, QWidget,QListWidgetItem,QPushButton, QHBoxLayout, QVBoxLayout, QLabel
from PySide2.QtGui import QFontMetrics, QIcon
from PySide2.QtCore import QSize, Qt
from personlized_widget.p_widget import *
from functools import partial
import shutil

class Associate:
    def __init__(self, program_info_df, ouput_num_f):
        self.num = ouput_num_f
        self.df = program_info_df
        self.names = nan_to_sign(list(self.df['Name'].values))
        self.ch_names = nan_to_sign(list(self.df['Chinese Name'].values))
        self.description = nan_to_sign(list(self.df['Description'].values))
        self.exe_path = nan_to_sign(list(self.df['EXE Path'].values))
    # To Associate subdirectory of certain path
    def path(self, prompt_f):
        if not prompt_f:
            return []
        # prompt is a specific file path
        if os.path.exists(prompt_f) and os.path.isfile(prompt_f):
            return []
        # prompt is a directory
        if os.path.exists(prompt_f):
            return os.listdir(prompt_f)
        # prompt is a unfilled diretory
        sup_path = os.path.dirname(prompt_f)
        dir_name_n = prompt_f.split('\\')[-1]
        if not os.path.exists(sup_path):
            return []
        else:
            list_1f = sorted([dir_if for dir_if in os.listdir(sup_path) if dir_name_n in dir_if], key=lambda x:x.index(dir_name_n))
            list_2f = sorted([dir_if for dir_if in os.listdir(sup_path) if dir_name_n.lower() in dir_if.lower()], key=lambda x:(x.lower()).index(dir_name_n.lower()))
            return rm_dp_list_elem(list_1f+list_2f, reverse=False)
    
    # To associate a programme name of prompt
    def name(self, prompt_f):
        if not prompt_f:
            return []
        try:
            output_name = sorted([name_i for name_i in self.names if prompt_f.lower() in name_i.lower()], key=lambda s: (s.lower().index(prompt_f.lower()))/len(s))
            output_chname = sorted([ch_name_i for ch_name_i in self.ch_names if prompt_f.lower() in ch_name_i.lower()], key=lambda s: (s.lower().index(prompt_f.lower()))/len(s))
            output_des = [self.names[self.description.index(dsp_name_i)] for dsp_name_i in self.description if prompt_f.lower() in dsp_name_i.lower()]
            output_chname_t = [i for i in output_chname if self.names[self.ch_names.index(i)] not in output_name]
            output_des_t = [i for i in output_des if self.ch_names[self.names.index(i)] not in output_chname]
            return rm_dp_list_elem(output_name+output_chname_t+output_des_t, reverse=False)[0:self.num]
        except Exception as e:
            return []
    
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
                return os.path.join(prompt_f, os.listdir(prompt_f)[0])
            else:
                return None
        else:
            sup_path = os.path.dirname(prompt_f)
            if not os.path.exists(sup_path):
                return None
            else:
                name_wait_list = [name_if for name_if in os.listdir(sup_path) if (name_if).lower().startswith((prompt_f.split('\\')[-1]).lower())]
                if len(name_wait_list) == 1:
                    return os.path.join(sup_path, name_wait_list[0])
                else:
                    return None
    
    # Automatically complete Name
    def fill_name(self, prompt_f):
        output_0 = [name_i for name_i in self.names if name_i.lower().startswith(prompt_f.lower())]
        output_1 = [ch_name_i for ch_name_i in self.ch_names if ch_name_i.lower().startswith(prompt_f.lower())]
        if len(output_0) == 1:
            return output_0[0]
        elif len(output_1) == 1:
            return output_1[0]
        

class AssociateList(QListWidget):
    def __init__(self, associate:Associate, config:Config_Manager, parent:Union[QMainWindow, QWidget]):  
        super(AssociateList, self).__init__(parent)
        self.up = parent
        self.ass = associate
        self.name = "associate_list"
        self.config = config.deepcopy()
        self.config.group_chose(mode="Launcher", widget=self.name)
        self.num = self.config.get(mode="max_ass_num", widget=None, obj='max_ass_num')
        self.ass_icon_list = self.config.get("icon_list", obj="path")
        self.ass_icon_name = [os.path.splitext(os.path.basename(i))[0] for i in self.ass_icon_list]
        self.ass_icon_default = self.config.get("default_icon", obj="path")

        # init
        self._personlize()
        self._inititem()

    def focusNextPrevChild(self, next):
    # inhibit focus move when pressing TAB
        # Override to prevent normal focus change
        return True
    
    def _personlize(self):
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
        self.setStyleSheet("""
        QScrollBar:vertical {
            background: transparent;
            width: 25px;
            margin: 5px;
        }

        QScrollBar::handle:vertical {
            background: #32CC99;
            min-height: 80px;
            border-radius: 7px;
        }

        QScrollBar::sub-line:vertical,
        QScrollBar::add-line:vertical,
        QScrollBar::sub-page:vertical,
        QScrollBar::add-page:vertical {
            background: none;
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
    def _changeicon(self, index_i):
        app_name = self.labels[index_i].text
        options = QFileDialog.Options()
        file_filter = "SVG Files (*.svg);;ICO Files (*.ico)"
        file_path, _ = QFileDialog.getOpenFileName(self, f"Choose '{app_name}' icon", "", file_filter, options=options)

        if not file_path:
            return
        file_type = os.path.splitext(file_path)[-1]
        dst = os.path.join(os.path.basename(self.ass_icon_list[0]), app_name+file_type)
        path = glob(os.path.join(os.path.basename(self.ass_icon_list[0]), app_name+".*"))
        for path_i in path:
            os.remove(path_i)
        shutil.copyfile(file_path, dst)
        self.buttons[index_i].setIcon(QIcon(dst))
    def _inititem(self):
        self.item_l = [QListWidgetItem() for i in range(self.num)]
        for item_i in self.item_l:
            self.addItem(item_i)
        self.font()
        het = self.config.get(name_f="het", mode="Common", widget="Size", obj=None)
        button_size = QSize(het, het)
        self.buttons = [YohoPushButton(self.ass_icon_default, button_size, an_type="shake") for i in range(self.num)]
        label_font = self.font()
        self.labels = [AutoLabel(text="Default", font=label_font) for i in range(self.num)]
        for i in range(self.num):
            self.add_custom_item(self.item_l[i], self.buttons[i], self.labels[i])
        
        for item_i in self.item_l:
            item_i.setHidden(True)
        for order_i, button_i in enumerate(self.buttons):
            button_i.clicked.connect(partial(self._changeicon, index_i=order_i))
        
    def _geticon(self, name:str):
        if name in self.ass_icon_name:
            return QIcon(self.ass_icon_list[self.ass_icon_name.index(name)])
        else:
            return QIcon(self.ass_icon_default)
    
    def add_custom_item(self, item:QListWidgetItem, button_f:QPushButton, text_f:QLabel):
        widget_i = QWidget()
        layout_i = QHBoxLayout()
        layout_i.addWidget(button_f)
        layout_i.addWidget(text_f)
        widget_i.setLayout(layout_i)
        self.setItemWidget(item, widget_i)

    # to update associate_words
    def update_associated_words(self):
        if self.up.mode != "Launcher":
            return
        current_text:str = self.up.get_input()
        if is_path(current_text):
            matching_words = self.ass.path(current_text)
        else:
            if ';' not in current_text:
                matching_words = self.ass.name(current_text)
            else:
                matching_words = self.ass.multi_pro_name(current_text.split(';'))

        for i in range(self.num):
            if i >= len(matching_words):
                self.item_l[i].setHidden(True)
                continue
            text_i = matching_words[i]
            icon_i = self._geticon(text_i)
            self.labels[i].setText(text_i)
            self.buttons[i].setIcon(icon_i)
        
        try:
            font_metrics = QFontMetrics(self.font())
            width_f = max([font_metrics.boundingRect(' '+word).width() + 60 for word in matching_words])
            width_f = min(width_f, (self.window_size_set['Launcher']['input_box'][-2]-self.size_set['gap'])//2)
            self.setMinimumWidth(width_f)
            self.setMaximumWidth(width_f)
        except Exception:
            pass

class SwitchButton(QComboBox):
    def __init__(self, parent: QMainWindow, mode_list:list[str], config:Config_Manager) -> None:
        super().__init__(parent)
        self.up = parent
        self.name = "switch_button"
        self.config = config.deepcopy()
        self.config.group_chose(mode="MainWindow", widget=self.name)
        self._initUI()
        self.mode_list = mode_list
        self.gem = self.config.get(self.name, widget=None, obj="Size")
        self.currentIndexChanged.connect(self._change_length)  # 连接信号槽
    def _initUI(self):
        for model_if in self.mode_list:
            self.addItem(model_if)
        self.setCurrentIndex(self.up.mode)

        font_f = self.config.get("Font", obj=None)
        self.setFont(font_f)
        font_metrics = QFontMetrics(self.font())
        w_f = font_metrics.boundingRect(self.up.mode).width() + 30  # 加上一些额外空间，你可以根据需要修改
        self.setGeometry(self.gem[0], self.gem[1], w_f, self.gem[-1])
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
        self.setGeometry(self.gem[0], self.gem[1], w_f, self.gem[-1])

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

        self._initbuttons()
        self.max_button.clicked.connect(self.max_click)
        self.setLayout(self.layout_1)
        self.setGeometry(*tuple(self.geom))
        

    def _initbuttons(self):
        size_i = QSize(int(1.5*self.up.het), 1.5*self.up.het)
        self.max_path = self.config.get('maximum', obj="path")
        self.min_path = self.config.get('minimum', obj="path")
        self.middle_path = self.config.get('close', obj="path")
        self.close_path = self.config.get('middle', obj="path")

        self.max_button = YohoPushButton(QIcon(self.max_path), size_i, None)
        self.min_button = YohoPushButton(QIcon(self.min_path), size_i, None)
        self.close_button = YohoPushButton(QIcon(self.close_path), size_i, None)
        self.layout_1.addItem(self.max_button)
        self.layout_1.addItem(self.min_button)
        self.layout_1.addItem(self.close_button)
    
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
        self.setStyleSheet("border-radius: 20px; padding-left: 20px;")  # smooth four angle
        # self.up.input_box.textChanged.connect(self.up.update_associated_words)
        # self.up.input_box.returnPressed.connect(self.up.confirm_action)
        self.setFont(self.config.get("main", obj="font"))
        gemo = self.config.get(self.name, widget=None, obj="Size")
        self.setGeometry(*gemo)

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
        self._initpara()
        self._initUI()

    def _initpara(self):
        self.v_num = self.config.get('vertical_button_num', mode="Common", widget=None, ob=None)
        self.h_num = self.config.get('horizontal_button_num', mode="Common", widget=None, ob=None)
        self.h_layout = [QHBoxLayout() for _ in range(self.v_num)]
        self.df_path = self.config.get("setting_xlsx", obj='path')
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
            for h_i in range(self.h_num):
                if index_f < self.num_real:
                    name, icon, path = self.df.iloc[0:3, index_f]
                else:
                    name = "Unset"
                    icon = self.config.get('default_button_icon', obj='path')
                    path = 'C:\\'
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
                self.h_layout[v_i].addItem(button_i)
                self.h_layout[v_i].addItem(label_i)
            self.layout_0.addLayout(self.h_layout[v_i])
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
                    path = 'C:\\'
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
        self._windowset()
        self._initpara()
        self._initUI()

    def _windowset(self):
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("Shortcut Setting")
        self.setWindowIcon(QIcon(self.up.path_set['Shortcut Setting']['window_button']))
    
    def _initpara(self):
        # init other para
        self.title_i = self.config.get('window_title', obj='name')
        self.v_num = self.config.get('vertical_button_num', mode="Common", widget=None, ob=None)
        self.h_num = self.config.get('horizontal_button_num', mode="Common", widget=None, ob=None)
        self.num_t = int(self.v_num*self.h_num)
        self.data_load = [{}]*self.num_t
        self.objs = []
        
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
        self.config.get('')

        self.col_coordinate_icon = self.config.get('col_coordinate_icon')
        self.col_name_icon = self.config.get('col_name_icon')
        self.col_icon_icon = self.config.get('col_icon_icon')
        self.col_path_icon = self.config.get('col_path_icon')
        self.col_search_icon = self.config.get('col_search_icon')

        # size para
        self.config.group_chose(obj='size')
        for i in range(4):
            setattr(self, f"colwidth_{i}", self.config.get(f"colwidth_{i}"))

    def _initUI(self):
        x, y, w, h = self.up.get_geometry(self.up)
        x_1, y_1, w_1, h_1 = self.up.window_size_set_ori_data['Launcher']['main_window']
        self.w_1 = int(w_1*15/16)
        self.h_1 = int(h_1*16/15)
        self.setGeometry(x+w//2-w_1//2, y+h//2-h_1//2, self.w_1, self.h_1)
        
        self.layout_0 = QVBoxLayout()
        self._init_title()
        self._init_colname()
        self.init_obj()
        self.init_button()
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
        output = []
        # coordinate define
        coordinate_name = f"{(index+1)%self.h_num}, {(index+1)//self.h_num+1}"
        
        cor_label = AutoLabel(coordinate_name, self.coordinate_label_font)

        cor_label.setStyleSheet('''background-color: transparent;
                                        border:none''')  # 设置标题透明背景
        output.append(cor_label)

        name_if = self.df.iloc[index, 0]
        name_if = name_if if isinstance(name_if, str) else 'Uncertain'
        name_edit = QLineEdit(name_if)
        name_edit.setFixedSize(*self.colwith_1)
        name_edit.setFont(self.app_name_label_font)
        name_edit.setStyleSheet("background-color: transparent;")
        output.append(name_edit)

        
        icon_if = self.df.iloc[index, 1] if is_path(self.df.loc[index, 1], True) else self.default_app_icon
        icon_button = YohoPushButton(icon_if, self.up.het, an_time="resize")
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
        
        exe_f = self.df.iloc[index, 2]
        exe_edit = QLineEdit()
        exe_edit.setFixedSize(*self.colwidth_3)
        check_f = partial(self._check_path_validity, line_edit=exe_edit)
        exe_edit.textChanged.connect(check_f)
        exe_edit.setPlaceholderText(exe_f)
        exe_edit.setFont(font_get(self.up.font_set['opto_setting_exe_edit']))
        exe_edit.setStyleSheet("background-color: transparent;")
        output.append(exe_edit)
        

        folder_button = YohoPushButton(self.default_folder_icon, self.colwidth_4[1])
        folder_button.setFixedSize(*self.colwidth_4)
        folder_button.setStyleSheet("background-color: transparent;border:none")
        output.append(folder_button)
        return output

    def init_obj(self):
        obj_layout = QVBoxLayout()
        num_t = int(self.v_num*self.h_num)
        for i_f in range(num_t):
            self.data_load[i_f] = {'Display_Name':None,
                                   'Icon_Path':None,
                                   'EXE_Path':None}
            layout_row = QHBoxLayout()
            
        
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
            background: transparent; /* 将滚动槽的背景色设置为透明 */
            }
        """)

    def init_button(self):
        button_layout = QHBoxLayout()
        # 创建确认和取消按钮
        confirm_button = QPushButton("Confirm")
        confirm_button.setFont(font_get({'Family':'Jetbrains Mono', 'PixelSize':30, 'Weight':70}))
        confirm_button.clicked.connect(self.confirm_action)
        confirm_button.setStyleSheet('''
        QPushButton {
            padding: 10px;
            color: #fff;
            border: none;
            border-radius: 10px;
            background-color: #286FB1;
        }

        QPushButton:hover {
            background-color: #2CC1E1; /* 设置悬停时的颜色 */
        }
        
        QPushButton:pressed {
                background-color: #349179;
            }
        
        ''')
        
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setFont(font_get({'Family':'Jetbrains Mono', 'PixelSize':30, 'Weight':70}))
        cancel_button.clicked.connect(self.cancel_action)
        cancel_button.setStyleSheet('''
        QPushButton {
            padding: 10px;
            color: #fff;
            border: none;
            border-radius: 10px;
            background-color: #C60618;
        }

        QPushButton:hover {
            background-color: #FF4A6C; /* 设置悬停时的颜色 */
        }
        
        QPushButton:pressed {
            background-color: #349179;
        }
        
        ''')
        
        name_1 = "Launcher"
        launcher_excel_open_button = QPushButton(name_1)
        launcher_excel_open_button.setFont(font_get({'Family':'Jetbrains Mono', 'PixelSize':30, 'Weight':70}))
        func_1 = partial(self.open_func, sign_f=name_1)
        launcher_excel_open_button.clicked.connect(func_1)
        launcher_excel_open_button.setStyleSheet('''
        QPushButton {
            padding: 10px;
            color: #fff;
            border: none;
        }
        QPushButton {
            border-radius: 10px;
            background-color: #44BBB1;
        }

        QPushButton:hover {
            background-color:#2CE1B3; /* 设置悬停时的颜色 */
        }
        
        QPushButton:pressed {
            background-color: #349179;
        }
        
        ''')
        
        name_2 = "Shortcut"
        shortcut_excel_open_button = QPushButton(name_2)
        shortcut_excel_open_button.setFont(font_get({'Family':'Jetbrains Mono', 'PixelSize':30, 'Weight':70}))
        func_2 = partial(self.open_func, sign_f=name_2)
        shortcut_excel_open_button.clicked.connect(func_2)
        shortcut_excel_open_button.setStyleSheet('''
            QPushButton {
                padding: 10px;
                color: #fff;
                border: none;
                border-radius: 10px;
                background-color: #44BBB1;
            }

            QPushButton:hover {
                background-color: #2CE1B3; /* 设置悬停时的颜色 */
            }
            QPushButton:pressed {
                background-color: #349179;
            }
            ''')
        
        button_layout.addWidget(launcher_excel_open_button)
        button_layout.addWidget(shortcut_excel_open_button)
        button_layout.addWidget(confirm_button)
        button_layout.addWidget(cancel_button)
        
        self.layout_0.addLayout(button_layout)
    
    def confirm_action(self):
        df_n = self.dict_trans()
        print(df_n)
        self.up.shortcut_df = df_n
        # relaunch button set
        self.up.shortcut_button.close()
        self.up.shortcut_button = Shortcuts(self.up)
        self.hide()
        # write in dataframe
        wb = openpyxl.load_workbook(self.up.path_set['Shortcut Setting']['shortcut_set'], data_only=True)
        ws = wb.worksheets[0]
        for row_i in range(len(df_n)):
            for col_i in range(3):
                ws.cell(row=row_i+2, column=col_i+1, value=df_n.iloc[row_i, col_i])
        wb.save(self.up.path_set['Shortcut Setting']['shortcut_set'])
        self.close()

    
    def dict_trans(self):
        df_copy = copy.deepcopy(self.df)
        for key_i, dict_i in self.data_load.items():
            for key_ii, value_i in dict_i.items():
                if key_ii in ['Display_Name', 'EXE_Path']:
                    if value_i.text():
                        df_copy.at[key_i, key_ii] = value_i.text()
                    else:
                        df_copy.at[key_i, key_ii] = self.df.loc[key_i, key_ii]
            for key_ii, value_i in dict_i.items():
                if key_ii == 'Icon_Path':
                    format_n = value_i.split('.')[-1]
                    obj_name = df_copy.loc[key_i, 'Display_Name']
                    path_new = os.path.join(os.path.dirname(self.icon_set_path[0]), f'{obj_name}.{format_n}')
                    if value_i != path_new:
                        shutil.copy(value_i, path_new)
                    df_copy.at[key_i, key_ii] = path_new
        return df_copy
    
    def cancel_action(self):
        self.close()
    
    def open_func(self, sign_f):
        if sign_f == 'Launcher':
            path_f = self.up.path_set['Launcher Mode']['launcher_set']
        elif sign_f == 'Shortcut':
            path_f = self.up.path_set['Shortcut Setting']['shortcut_set']
        else:
            path_f = ''
        subprocess.Popen(['explorer', path_f])
    # animation define function
    def animations(self, button_f, size_ori, size_dst, func_f):
        self.animation1 = QPropertyAnimation(self, targetObject=button_f, propertyName=b'iconSize')
        self.animation1.setDuration(120)
        # self.animation1.setTargetObject(button_f)
        self.animation1.setStartValue(QSize(size_ori, size_ori))
        self.animation1.setEndValue(QSize(size_dst, size_dst))
        self.animation1.finished.connect(func_f)
        self.animation1.start()
    # button click total func
    def button_flash(self):
        button_f = self.sender()
        func_f = self.effect_dict[button_f.objectName()]
        size_ori = button_f.iconSize().width()
        size_dst = int(button_f.iconSize().width()*0.5)
        self.animations(button_f, size_ori, size_dst, lambda:self.animations(button_f, size_dst, size_ori, func_f))
    # icon click conduct function
    def icon_click(self, button_f, row_f):
        filename_f, _ = QFileDialog.getOpenFileName(None, "Chose your Icon", "", "Photo File (*.png *.jpg *.bmp *.jepg *.svg *ico)")
        if not filename_f:
            return
        self.data_load[row_f]['Icon_Path'] = filename_f.replace('/', '\\')
        button_f.setIcon(QIcon(filename_f))
        button_f.setIconSize(QSize(60, 60))
    # check exe path validity
    def _check_path_validity(self, text, line_edit):
        text_f = line_edit.text()
        if os.path.exists(text_f) or (not text_f):
            line_edit.setStyleSheet("border: 1px solid grey; background-color: transparent;")  # 路径不存在，变红
        elif os.path.isabs(text_f):
            line_edit.setStyleSheet("border: 3px solid #F0F411; background-color: transparent;")  # 路径不存在，变红
        else:
            line_edit.setStyleSheet("border: 3px solid #EE1515; background-color: transparent;")  # 路径存在，变黄
    # excel path search
    def exe_search(self, line_f):
        file_path_f, _ = QFileDialog.getOpenFileName(None, "Chose Your EXE Path", "", "All Files (*);;Folders")
        if file_path_f:
            line_f.setText(file_path_f.replace('/', '\\').strip())

    





    



    


