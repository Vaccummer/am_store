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

class UIShortcutSetting(QWidget):
    def __init__(self, parent:QMainWindow, config:Config_Manager):
        super().__init__()
        self.up = parent
        self.name = 'shortcut_obj'
        self.config = config.deepcopy().group_chose(mode="Launcher", widget=self.name)
        self._initpara()
        self._windowset()
        self._initUI()
    
    def _windowset(self):
        self.drag_position = None
        self.edge_drag = None
        self.edge_threshold = 20
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("Shortcut Setting")
        UIUpdater.set(atuple('Launcher','shortcut_obj','path','taskbar_icon'), self.setWindowIcon,type_f='icon')
        # For mouse control
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.isNearEdge(event.pos()):
                self.edge_drag = event.pos()
                self.original_geometry = self.geometry()
                event.accept()
            else:
                # x, y, w, h = self.get_geometry(self)
                # if event.y() >y+h or event.x() > x+w:
                if True:
                    self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
                    event.accept()
        else:
            super().mousePressEvent(event)
    def mouseMoveEvent(self, event):
        # if self.edge_drag:
        #     self.resizeWindow(event.pos())
        if self.drag_position and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
        else:
            super().mouseMoveEvent(event)
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = None
            self.edge_drag = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    def isNearEdge(self, pos):
        x, y, w, h = self.get_geometry(self)
        return (
            pos.x() > w - self.edge_threshold or
            pos.y() > h - self.edge_threshold
        )
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # 绘制带有圆角和渐变的窗口背景
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(113, 148, 139))
        gradient.setColorAt(1, QColor(162, 245, 224))
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 20, 20)
    @staticmethod
    def get_geometry(window_f):
        geom_f = window_f.geometry()
        return[geom_f.x(), geom_f.y(), geom_f.width(), geom_f.height()]
    
    def _set_w(self, obj, size:List[Union[int,bool]]):
        if size[0]:
            obj.setMinimumWidth(size[0])
        if size[1]:
            obj.setMaximumWidth(size[1])
    
    def _initpara(self):
        # init other para
        self.title_i = atuple('Launcher', self.name, 'name', 'window_title')
        self.v_num = self.config.get('vertical_button_num', mode="Launcher", obj=None)
        self.h_num = self.config.get('horizontal_button_num', mode="Launcher", obj=None)
        self.num_t = int(self.v_num*self.h_num)
        self.objs = []
        self.option_button = []
        self.line_height = atuple('Launcher', self.name, 'Size', 'line_height')
        self.colname_margin = atuple('Launcher', self.name, 'Size', 'colname_margin')
        pre = ['Launcher', self.name, 'font']
        self.window_title_font = atuple(pre+['window_title'])
        self.coordinate_label_font = atuple(pre+['coordinate_label'])
        self.app_name_label_font = atuple(pre+['app_name_label'])
        self.exe_lineedit_font = atuple(pre+['exe_lineedit'])
        self.option_button_font = atuple(pre+['option_button'])
        self.title_style = atuple('Launcher', self.name, 'style', 'setting_title')
        self.col_style = atuple('Launcher', self.name, 'style', 'column_label')
        self.cor_style = atuple('Launcher', self.name, 'style', 'coordinate_label')
        self.icon_button_style = atuple('Launcher', self.name, 'style', 'icon_button')
        self.app_name_edit_style = atuple('Launcher', self.name, 'style', 'app_name_edit')
        self.exe_lineedit_style = atuple('Launcher', self.name, 'style', 'exe_lineedit')
        self.tooltip_style = atuple('Launcher', self.name, 'style', 'exe_tip')
        self.search_button_style = atuple('Launcher', self.name, 'style', 'folder_search_button')
        # init path
        pre = ['Launcher', self.name, 'path']
        self.manager:ShortcutsPathManager = self.up.shortcut_data
        self.df = self.manager.df
        self.taskbar_icon = atuple(pre+['taskbar_icon'])
        self.button_icons = atuple(pre+['button_icons'])
        self.default_app_icon = atuple(pre+['default_app_icon'])
        self.default_folder_icon = atuple(pre+['default_folder_icon'])

        self.col_coordinate_icon = atuple(pre+['col_coordinate_icon'])
        self.col_name_icon = atuple(pre+['col_name_icon'])
        self.col_icon_icon = atuple(pre+['col_icon_icon'])
        self.col_path_icon = atuple(pre+['col_path_icon'])
        self.col_search_icon = atuple(pre+['col_search_icon'])

        # size para
        pre = ['Launcher', self.name, 'Size']
        self.title_height = atuple(pre+['title_height'])
        self.col_label_height = atuple(pre+['col_label_height'])
        for i in range(5):
            setattr(self, f"colwidth_{i}", atuple(pre+[f'colwidth_{i}']))
    
    def showWin(self):
        up_geom = self.up.geometry()
        x, y, w, h = up_geom.x(), up_geom.y(), up_geom.width(), up_geom.height()
        w_1, h_1 = self.config[atuple('Launcher', self.name, 'Size', 'setting_window_size')]
        x_t = x + w//2 - w_1//2
        y_t = y + h//2 - h_1//2
        self.setGeometry(x_t, y_t, w_1, h_1)
        self.show()
        self.raise_()
    
    def _initUI(self):
        ## UI set
        self.layout_0 = QVBoxLayout()
        self._init_title()
        self._init_colname()
        self._init_obj()
        self._init_action_button()
        self.setLayout(self.layout_0)

    def _init_title(self):
        title_label = AutoLabel(text=self.title_i, font=self.window_title_font, style_config=self.title_style, height=self.title_height)
        title_label.setAlignment(Qt.AlignCenter)
        self.layout_0.addWidget(title_label)
    
    def _init_colname(self):
        self.layout_col = QHBoxLayout()
        UIUpdater.set(self.colname_margin,self.layout_col.setContentsMargins,'margin')
        self.config.group_chose(obj="name")

        col_names_size = {'coordinate':self.colwidth_0, 
                          'name':self.colwidth_1, 
                          'icon':self.colwidth_2, 
                          'path':999, 
                          'search':self.colwidth_4}
        
        for name_i, size_i in col_names_size.items():
            icon_f = getattr(self, f"col_{name_i}_icon")
            if name_i != 'path':
                col_label = AutoLabel(text='', font=self.app_name_label_font, style_config=self.col_style, 
                                      icon_f=icon_f,height=self.col_label_height, width=size_i)
            else:
                col_label = AutoLabel(text='', font=self.app_name_label_font, style_config=self.col_style,
                                      icon_f=icon_f,height=self.col_label_height)
            # self._set_w(col_label, size_i)
            col_label.setAlignment(Qt.AlignCenter)
            self.layout_col.addWidget(col_label)
        
        self.layout_0.addLayout(self.layout_col)
    
    def _get_obj(self, index:int):
        if index < self.df.shape[0]:
            name_if = self.df.iloc[index, 0]
            icon_if = self.manager.geticon(name_if)
            exe_f = self.df.iloc[index, 2]
        else:
            name_if = ''
            icon_if = self.default_app_icon
            exe_f = ''
        output = []
        # coordinate define
        coordinate_name = f"({(index+1)%self.h_num},{(index+1)//self.h_num+1})"
        
        cor_label = AutoLabel(text=coordinate_name, font=self.coordinate_label_font,style_config=self.cor_style, 
                              width=self.colwidth_0, height=self.line_height)
        output.append(cor_label)

        icon_button = YohoPushButton(icon_i=icon_if, style_config=self.icon_button_style, size_f=self.line_height)
        icon_button.setProperty('path', '')
        output.append(icon_button)
        
        name_if = name_if if isinstance(name_if, str) else ''
        name_edit =AutoEdit(text=name_if, font=self.app_name_label_font, style_d=self.app_name_edit_style,
                            height=self.line_height, width=self.colwidth_2)
        output.append(name_edit)

        exe_edit = ExePathLine(style_d=self.exe_lineedit_style, height_f=self.line_height, 
                               place_holder=exe_f, font=self.exe_lineedit_font,tooltip_style=self.tooltip_style)
        output.append(exe_edit)
        
        folder_button = YohoPushButton(icon_i=self.default_folder_icon, style_config=self.search_button_style,
                                       size_f=self.line_height)
        output.append(folder_button)
        return output

    def _init_obj(self):
        obj_layout = QVBoxLayout()
        num_t = int(self.v_num*self.h_num)
        for i_f in range(num_t):
            layout_h = QHBoxLayout()
            col_label, icon_button, name_edit,  exe_edit, folder_button = self._get_obj(i_f)
            self.objs.append({"index":i_f, "col_label":col_label, "name_edit":name_edit, 
                              "icon_button":icon_button, "exe_edit":exe_edit, "folder_button":folder_button})
            icon_button.clicked.connect(partial(self._icon_change, index_f=i_f))
            #exe_edit.textChanged.connect(partial(self._check_path_validity, index_f=i_f))
            folder_button.clicked.connect(partial(self._exe_search, index_f=i_f))
            for i in [col_label, icon_button, name_edit, exe_edit, folder_button]:
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
        frame.setObjectName("OuterFrame")
        frame.setStyleSheet('''QFrame#OuterFrame {
                            background: transparent;
                            border-radius: 10px;
                            border: 1px solid gray;
                            background-color: transparent;
                        }''')  # Set border to the frame
        
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
        self.config.group_chose("Launcher", "shortcut_obj", "color")
        launcher_button = ColorfulButton("Launcher",
                                         [self.config[('launcher0')],
                                         self.config[('launcher1')],
                                         self.config[('launcher2')],],
                                         self.option_button_font, 
                                         self.line_height)
        launcher_button.setProperty('sign', 'launcher')
        launcher_button.clicked.connect(self._confirm_action)
        shortcut_button = ColorfulButton("Shortcut",
                                         [self.config['shortcut0'],
                                         self.config['shortcut1'],
                                         self.config['shortcut2']],
                                         self.option_button_font, 
                                         self.line_height)
        shortcut_button.setProperty('sign', 'shortcut')
        shortcut_button.clicked.connect(self._confirm_action)
        confirm_button = ColorfulButton("Confirm", 
                                        [self.config['confirm0'],
                                        self.config['confirm1'],
                                        self.config['confirm2']],
                                        self.option_button_font, 
                                        self.line_height
                                        )
        confirm_button.setProperty('sign', True)
        confirm_button.clicked.connect(self._confirm_action)

        cancel_button = ColorfulButton("Cancel",
                                       [self.config['cancel0'],
                                       self.config['cancel1'],
                                       self.config['cancel2']],
                                       self.option_button_font,
                                       self.line_height)
        cancel_button.setProperty('sign', False)
        cancel_button.clicked.connect(self._confirm_action)

        self.option_button.extend([launcher_button, shortcut_button, confirm_button, cancel_button])
        button_layout.addWidget(launcher_button)
        button_layout.addWidget(shortcut_button)
        button_layout.addWidget(confirm_button)
        button_layout.addWidget(cancel_button)
        self.layout_0.addLayout(button_layout)
class ShortcutSetting(UIShortcutSetting):
    def __init__(self, parent:QMainWindow, config:Config_Manager):
        super().__init__(parent, config)
        self.up = parent
        self.name = 'shortcut_obj'
        self.config = config.deepcopy().group_chose(mode="Launcher", widget='shortcut_obj')
        self.layout_0 = QVBoxLayout()
    
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
        name = self.objs[index_f]['name_edit'].text()
        options = QFileDialog.Options()
        file_filter = "SVG Files (*.svg);;ICO Files (*.ico)"
        dir_f = ''
        file_path, _ = QFileDialog.getOpenFileName(self, f"Choose '{name}' icon", dir_f, file_filter, options=options)
        if not file_path:
            return
        self.objs[index_f]['icon_button'].setIcon(QIcon(file_path))
        self.objs[index_f]['icon_button'].setProperty('path', file_path)
        return
        _, format_f = os.path.splitext(file_path)
        icon_path_ori = self.df.iloc[index_f, 1]
        icon_dir_ori = os.path.basename(icon_path_ori)
        name = self.objs[index_f]['name_edit'].text()
        dir_f = icon_dir_ori if os.path.exists(icon_dir_ori) else ""
        icon_dir = self.config.get("button_icons_dir", mode="Launcher", widget="shortcut_obj", obj="path")
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
        exe_dir_ori = os.path.dirname(exe_path_ori)
        name = self.objs[index_f]['name_edit'].text()
        dir_f = exe_dir_ori if os.path.exists(exe_dir_ori) else ""
        options = QFileDialog.Options()
        file_filter = "All Files (*);;Folders"
        file_path, _ = QFileDialog.getOpenFileName(self, f"Choose '{name}' launch file", dir_f, file_filter, options=options)
        if file_path:
            self.objs[index_f]['exe_edit'].setText(path_format(file_path))
    
    def _read_data(self):
        self.df = self.df.reset_index(drop=True)
        for i in range(self.num_t):
            name = self.objs[i]['name_edit'].text()
            exe_path = self.objs[i]['exe_edit'].text()
            icon_button = self.objs[i]['icon_button']
            if not name:
                continue
            if icon_button.property('path'):
                ext = os.path.splitext(icon_button.property('path'))[1]
                dst = os.path.join(self.button_icons, name+ext)
                if os.path.exists(dst):
                    os.remove(dst)
                shutil.copy2(icon_button.property('path'), dst)
                self.df.loc[i, 'Icon_Path'] = dst
            self.df.loc[i, 'EXE_Path'] = exe_path
            self.df.loc[i,'Display_Name'] = name
            
    def _confirm_action(self):
        button_t = self.sender()
        sign_f = button_t.property('sign')
        match sign_f:
            case "launcher":
                launcher_set = self.config.get('settings_xlsx', widget=None, obj='path')
                os.startfile(launcher_set)
                return
            case "shortcut":
                shortcut_set = self.config.get('setting_xlsx', widget='shortcut_obj', obj='path')
                os.startfile(shortcut_set)
                return 
            case False:
                self.close()
                return
            case True:
                pass
            case _:
                warnings.warn(f"ShorcutSetting._confirm_action recive illegal para {sign_f}")
                return
        
        self.hide()
        self._read_data()
        self.manager.save()
        self.up.shortcut_button.refresh()
        self.close()

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

class ExePathLine(AutoEdit):
    def __init__(self, style_d, tooltip_style, height_f:int, place_holder:str,font:QFont,):
        super().__init__(text='', font=font, style_d=style_d, height=height_f)
        self.setPlaceholderText(place_holder)
        self.place_holder = place_holder

        UIUpdater.set(style_d, self._loadColor)
        UIUpdater.set(tooltip_style, self._customTooltip)
        self.textChanged.connect(self._text_change)
    
    def _loadColor(self, style_d:atuple):
        self.background_color = style_d['background']
        self.warning_color = style_d['background_warning']
        self.error_color = style_d['background_error']

    def _customTooltip(self, tooltip_style:dict):
        self.setToolTip(self.place_holder)
        fm = tooltip_style.get('font_family', 'Consolas')
        size_f = tooltip_style.get('font_pt', 20)
        pd = tooltip_style.get('padding', [10,0,5,5])
        
        self.toolstyle_d = {
            'QToolTip':{
                'background-color': tooltip_style.get('background', '#FFFFFF'),
                'color': tooltip_style.get('color', '#161616'),
                'font': f'{size_f}pt "{fm}"',
                'border': tooltip_style.get('border', 'none'),
                'border-radius': f"{tooltip_style.get('border-radius', 10)}px",
                "padding": f"{pd[2]}px {pd[1]}px {pd[3]}px {pd[0]}px", 
                'opacity': tooltip_style.get('opacity', 100),
        }
        }
        self.tool_style = style_make(self.toolstyle_d)
        style_t = self.style_n + '\n' + self.tool_style
        self.setStyleSheet(style_t)

    def _text_change(self, text):
        self.setToolTip(text)
        if os.path.exists(text) or (not text):
            color_n = self.background_color
        elif os.path.isabs(text):
            color_n = self.warning_color
        else:
            color_n = self.error_color
        self.style_dict['QLineEdit']['background-color'] = color_n
        self.style_n = style_make(self.style_dict)
        style_t = self.style_n + '\n' + self.tool_style
        self.setStyleSheet(style_t)

class NameEdit(AutoEdit):
    def __init__(self, text_f:str,style_d,font:QFont, height:int,
                 ):
        super().__init__(text=text_f, font=font, height=height, style_d=style_d)
        self.style_d = style_d
    
    def _setStlye(self, sign_f:bool=True):
        style_dict = UIUpdater.config[self.style_d]
        if not style_dict:
            style_dict = {}
        if sign_f:
            self.style_dict['QLineEdit']['background-color'] = style_dict.get('background', '#F7F7F7')
        else:
            self.style_dict['QLineEdit']['background-color'] = style_dict.get('background_error', '#FF5733')
        self.style_n = style_make(self.style_dict)
        self.setStyleSheet(self.style_n)

class SheetControl(QTabBar):
    tab_operation = Signal(dict)
    def __init__(self, parent:QWidget, font_f:QFont, style_main:dict, style_menu:dict):
        super().__init__(parent)
        self.up = parent
        self.pre = ['Launcher', 'shortcut_obj', 'path']
        UIUpdater.set(font_f, self.setFont, 'font')
        UIUpdater.set(style_main, self.customStyle)
        self.setMovable(True) 
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_context_menu)
        self.setElideMode(Qt.ElideNone)
        self.tabMoved.connect(self.move_tab)
    
    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.win_move(0)
        else:
            self.win_move(1)
        event.accept()
    
    def win_move(self, index):
        scroll_buttons = self.findChildren(QToolButton)
        left_button = None
        right_button = None
        for button in scroll_buttons:
            if button.arrowType() == Qt.LeftArrow:
                left_button = button
            elif button.arrowType() == Qt.RightArrow:
                right_button = button
        if index == 0:
            left_button.click()
        else:
            right_button.click()
    
    def customStyle(self, style:dict):
        UIUpdater.set(style.get('main_height',60), self.setFixedHeight)
        bg_colors = style.get('background_colors', ["#F7F7F7", "#FFC300", "#FF5733"])
        font_colors = style.get('font_colors', ["#000000", "#000000", "#000000"])
        padding = style.get('padding', [0, 10, 0, 10])
        close_icon0 = UIUpdater.config[atuple(self.pre+['path', 'tab_close_icon0'])]
        if not close_icon0:
            close_icon0 = ''
        else:
            close_icon0 = close_icon0.replace('\\', '/')
        close_icon1 = UIUpdater.config[atuple(self.pre+['path', 'tab_close_icon1'])]
        if not close_icon1:
            close_icon1 = ''
        else:
            close_icon1 = close_icon1.replace('\\', '/')
        close_icon2 = UIUpdater.config[atuple(self.pre+['path', 'tab_close_icon2'])]
        if not close_icon2:
            close_icon2 = ''
        else:
            close_icon2 = close_icon2.replace('\\', '/')
        self.tab_style_d = {
            "QTabBar": {
                "border": style.get('main_border', "none"),
                "background": style.get('main_background', "transparent"),
                'border-radius': style.get('main_border_radius', 10),
            },
            "QTabBar::tab": {
                "margin-right": f"{style.get('tab_margin_right', 10)}px",
                "padding": f"{padding[2]}px {padding[1]}px {padding[3]}px {padding[0]}px", 
                "border-radius": f"{style.get('tab_border_radius', 10)}px",
                "height": f"{style.get('tab_height', 50)}px",
                "background": bg_colors[0],
                "color": font_colors[0],
                'border': style.get('tab_border', 'none'),
            },
            "QTabBar::tab:selected": {
                "background": bg_colors[2],
                "color": font_colors[2],    
            },
            "QTabBar::tab:hover": {
                "background": bg_colors[1],
                "color": font_colors[1],
            },
            "QTabBar::close-button": {
                "image": f"url({close_icon0});",
                "subcontrol-position": "right",
                "margin": "2px",
            },
            "QTabBar::close-button:hover": {
                "image": f"url({close_icon1});",
            },
            "QTabBar::close-button:pressed": {
                "image": f"url({close_icon2});",
            },
            "QTabBar::scroller": {
                "width": "0px",
                "height": "0px",
                "background-color": "transparent",
            }
        }
        self.sheetcontrol_stylesheet = style_make(self.tab_style_d)
        self.setStyleSheet(self.sheetcontrol_stylesheet)

    def _setMenuStyle(self, menu:QMenu, style:dict):
        padding = style.get('padding', [10,5,5,5])
        self.menu_style_d = {
            "QMenu": {
                "background-color": style.get('background', "#F7F7F7"),
                "border": style.get('border', "none"),
            },
            "QMenu::item": {
                "padding": f"{padding[2]}px {padding[1]}px {padding[3]}px {padding[0]}px",     # top, right, bottom, left
                "background-color": 'transparent',
                "color": style.get('font_color', "#000000"),
            },
            "QMenu::item:selected": {
                "background-color": style.get('background_hover', "#FF5733"),
                "color": style.get('font_color_hover', "#FFFFFF"),
            }
        }
        self.menu_stylesheet = style_make(self.menu_style_d)
        menu.setStyleSheet(self.menu_stylesheet)
    
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
        self._setMenuStyle(menu, self.config[atuple(self.pre+['style', 'menu'])])
        rename_action = menu.addAction("Rename")
        delete_action = menu.addAction("Delete")
        action = menu.exec_(self.mapToGlobal(position))
        if action == rename_action:
            self.tab_operation.emit({'action':'rename', 'index':index})
        elif action == delete_action:
            self.tab_operation.emit({'action':'delete', 'index':index})

    def move_tab(self, from_index, to_index):
        self.tab_operation.emit({'action':'move', 'from':from_index, 'to':to_index})

    def _rename(self, index:int, name_n):
        self.setTabText(index, name_n)
    
    def _delete(self, index:int):
        self.removeTab(index)
        
class BaseLauncherSetting(QWidget):
    def __init__(self, config:Config_Manager, parent:QMainWindow, manager:LauncherPathManager):
        super().__init__(parent)
        self.up = parent
        self.manager = manager
        self.config = config.deepcopy()
        self.name = 'LauncherSetting'
        self.config.group_chose(mode='Settings', widget=self.name)
        self._load_var()
        self._layout_load()
        self._process_ori_df()
    
    def _process_ori_df(self):
        self.df:dict[str:pandas.DataFrame] = self.manager.df
        self.df_l = []
        permit_col = ['Name', 'Chinese Name', 'EXE Path']
        for name_i, df_i in self.df.items():
            target_df = df_i.copy(deep=True)
            for col in target_df.columns:
                if col not in permit_col:
                    target_df.drop(col, axis=1, inplace=True)
            target_df.reset_index(drop=True, inplace=True)
            target_df.loc[:,'IconID'] = None
            self.df_l.append([name_i, target_df])
        self.df_n = self.df_l[0][1]

    def _load_var(self):
        self.num = int(self.config.get('ori_line_num', obj=None))
        self.line_num = 0

        pre = ['Settings', self.name, 'path']
        self.tmp_icon_folder = self.config.get('tmp_icon_folder', obj='path')
        self.default_app_icon = atuple('Launcher', 'shortcut_obj', 'path', 'default_button_icon')
        self.searcher_icon = atuple(pre+['searcher_icon'])
        self.add_button_icon = atuple(pre+['add_button_icon'])
        self.tab_delete_icon = atuple(pre+['tab_delete_icon'])
        self.add_sheet_button_icon = atuple(pre+['add_sheet_button_icon'])

        pre = ['Settings', self.name, 'font']
        self.name_font = atuple(pre+['name'])
        self.chname_font = atuple(pre+['chname'])
        self.exe_font = atuple(pre+['exe'])
        self.title_font = atuple(pre+['title'])
        self.number_font = atuple(pre+['number'])
        self.save_button_font = atuple(pre+['save_button'])
        self.discard_button_font = atuple(pre+['discard_button'])
        self.reset_button_font = atuple(pre+['reset_button'])
        self.tab_font = atuple(pre+['tab'])

        pre = ['Settings', self.name, 'Size']
        self.line_height = atuple(pre+['line_height'])
        self.add_button_margin = atuple(pre+['add_button_margin'])
        self.col_margin = atuple(pre+['col_margin'])
        self.nameedit_length = atuple(pre+['nameedit_max_length'])
        self.exeedit_min_length = atuple(pre+['exeedit_min_length'])
        self.bottom_margin = atuple(pre+['bottom_margin'])
        self.tab_height = atuple(pre+['tab_height'])
        self.line_spaing = atuple(pre+['line_spacing'])
        self.layout_spacing = atuple(pre+['layout_spacing'])
        self.frame_thickness = atuple(pre+['frame_thickness'])
        self.min_handle_height = atuple(pre+['min_handle_height'])
        self.numbercol_width = atuple(pre+['numbercol_width'])
        self.number_width = atuple(pre+['number_width'])
        self.tabbar_height = atuple(pre+['tabbar_height'])
        
        pre = ['Settings', self.name, 'style']
        self.icon_button_style = atuple(pre+['icon_button'])
        self.nameedit_style = atuple(pre+['name_edit'])
        self.exeedit_style = atuple(pre+['exe_edit'])
        self.tooltip_style = atuple(pre+['exe_tip'])
        self.folder_button_style = atuple(pre+['folder_search_button'])
        self.add_button_style = atuple(pre+['add_line_button'])
        self.tab_style = atuple(pre+['sheet_control'])
        self.meunu_style = atuple(pre+['menu'])
        self.tab_add_style = atuple(pre+['tab_add_button'])
        self.save_button_style = atuple(pre+['save_button'])
        self.reset_button_style = atuple(pre+['reset_button'])
        self.title_style = atuple(pre+['title'])
        self.frame_style = atuple(pre+['outer_frame'])
        self.scroll_area_style = atuple(pre+['scroll_bar'])
        self.number_style = atuple(pre+['number_label'])

    def _layout_load(self):
        self.layout_0 = amlayoutV(align_h='c', spacing=5)
        UIUpdater.set(self.layout_spacing, self.layout_0.setSpacing)
        self.setLayout(self.layout_0)
        self.objs_l = {}
        self.widget_l = []
        self.tab_index = 0

    def _get_default_df(self, group:str):
        # ['Name', 'Chinese Name', 'Description', 'EXE Path', 'Group']
        data = OrderedDict([['Name', ['']], ['Chinese Name', ['']], ['EXE Path', ['']], ['Group', [group]], ['IconID',[None]]])
        return pandas.DataFrame(data)
class UILauncherSetting(BaseLauncherSetting):
    def __init__(self, config:Config_Manager, parent:QMainWindow, manager:LauncherPathManager):
        super().__init__(config, parent , manager)
        self._initUI()
    
    def _initUI(self):
        self._init_tiles()
        self._init_layout()
        self._init_multi_line()
        self._init_add_line()
        self._init_bottom_control()
        add_obj(self.add_button_lo, parent_f=self.obj_layout)
        self.obj_layout.addStretch()
        add_obj(self.title_layout, self.scroll_area,parent_f=self.layout_0)
        self.layout_0.addLayout(self.bottom_layout)
        self._line_fresh(0)
    
    def _init_layout(self):
        self.obj_layout = amlayoutV()
        UIUpdater.set(self.line_spaing, self.obj_layout.setSpacing)
        # Create a scroll area and add the content layout to it
        self.scroll_content = QWidget()  # Create a widget to contain the layout
        self.scroll_content.setLayout(self.obj_layout)
        self.frame = QFrame()  # Create a frame to contain the scroll area
        self.frame_layout = QVBoxLayout()
        self.frame_layout.addWidget(self.scroll_content)
        self.frame_layout.setContentsMargins(0, 0, 0, 0)
        self.frame.setLayout(self.frame_layout)
        self.frame.setObjectName("OuterFrame")
        UIUpdater.set(self.frame_style, self._frameStyle)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("myScrollArea")
        self.scroll_area.setWidget(self.frame)  # Set the frame as the widget of the scroll area
        self.scroll_area.setWidgetResizable(True)
        UIUpdater.set(self.scroll_area_style,
                      self._scrollAreaStyle,
                      alist())
    
    def _frameStyle(self, frame_style:dict):
        self.frame_style_d = {
            'QFrame#OuterFrame':{
                'background': frame_style.get('background', 'transparent'),
                'border-radius': f"{frame_style.get('border-radius', 10)}px",
                'border': frame_style.get('border', '5px solid gray'),
            }
        }
        self.frame_stylesheet = style_make(self.frame_style_d)
        self.frame.setStyleSheet(self.frame_stylesheet)

    def _scrollAreaStyle(self, scroll_style:dict):
        orbit_color = scroll_style.get('orbit_color', 'transparent')
        background_colors = scroll_style.get('background_colors', ["#F7F7F7", "#FFC300", "#FF5733"])
        border_radius = scroll_style.get('border_radius', 10)
        min_height = scroll_style.get('min_height', 20)
        width = scroll_style.get('width', 20)
        border = scroll_style.get('border', 'none')

        self.scroll_area_style_d = {
            "QScrollArea#myScrollArea": {
                "background": 'transparent',
                "border": 'none',
            },
            "QScrollBar": {
                "border": border,
                "background": orbit_color,
                "width": f"{width}px",
                "margin": "5px",
                "border-radius": f"{border_radius}px",
            },
            "QScrollBar::handle": {
                "background": background_colors[0],
                "min-height": f"{min_height}px",
                "border-radius": f"{border_radius}px",
            },
            "QScrollBar::handle:vertical:hover": {
                "background": background_colors[1],
            },
            "QScrollBar::handle:selected": {
                "background": background_colors[2],
            },
            "QScrollBar::add-line": {
                "background": 'transparent',
                "height": "0px",
                "subcontrol-position": "bottom",
                "subcontrol-origin": "margin",
            },
            "QScrollBar::sub-line": {
                "background": 'transparent',
                "height": "0px",
                "subcontrol-position": "top",
                "subcontrol-origin": "margin",
            },
            "QScrollBar::sub-page, QScrollBar::add-page": {
                "background": 'transparent',
            }
        }
        self.scroll_stylesheet = style_make(self.scroll_area_style_d)
        self.scroll_area.setStyleSheet(self.scroll_stylesheet)

    def _init_tiles(self):
        self.title_layout = amlayoutH()
        UIUpdater.set(self.col_margin, self.title_layout.setContentsMargins, 'margin')
        self.titles = ['number_col', 'icon_col', 'name_col', 'chname_col','exe_col', 'searcher']
        width_l = [self.numbercol_width, self.line_height, self.nameedit_length, self.nameedit_length, self.exeedit_min_length, self.line_height]
        for i, title_i in enumerate(self.titles):
            icon_i = atuple('Settings', 'LauncherSetting', 'path', f'{title_i}_icon')
            col_i = AutoLabel(text='', font=self.title_font,icon_f=icon_i, width=width_l[i], style_config=self.title_style)
            if self.titles[i] == 'exe_col':
                col_i.setMinimumWidth(0)
                col_i.setMaximumWidth(99999)
            col_i.setAlignment(Qt.AlignCenter)
            setattr(self, title_i, col_i)
            self.title_layout.addWidget(getattr(self, title_i))

    def _init_single_line(self, index_f:int, df:pandas.DataFrame=None, default:bool=False, insert:bool=False):
        if default is not False:
            icon_i = self.default_app_icon
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
        
        nummber_w = AutoLabel(font=self.number_font,
                              text=str(index_i),
                              width=self.number_width,
                              height=self.line_height,
                              style_config=self.number_style
                              )

        icon_w = YohoPushButton(icon_i=icon_i, size_f=self.line_height, style_config=self.icon_button_style)
        icon_w.setProperty('index', index_i)
        icon_w.setProperty('icon_path', '')
        icon_w.clicked.connect(lambda: self._change_icon(index_i))
        name_label = NameEdit(text_f=name, style_d=self.nameedit_style, height=self.line_height, font=self.name_font)
        name_label.setProperty('index', index_i)
        name_label.setProperty('type', 'name')
        UIUpdater.set(self.nameedit_length, name_label.setMaximumWidth)
        name_label.textChanged.connect(self.name_edit_change)
        chname_label = NameEdit(text_f=chname, style_d=self.nameedit_style, height=self.line_height, font=self.name_font)
        chname_label.setProperty('index', index_i)
        chname_label.setProperty('type', 'chname')
        chname_label.textChanged.connect(self.name_edit_change)
        exe_edit = ExePathLine(style_d=self.exeedit_style,tooltip_style=self.tooltip_style, height_f=self.line_height, 
                               place_holder=exe_path, font=self.exe_font)
        exe_edit.setProperty('index', index_i)
        UIUpdater.set(self.exeedit_min_length, exe_edit.setMinimumWidth)
        folder_button = YohoPushButton(icon_i=self.searcher_icon, size_f=self.line_height, style_config=self.folder_button_style)
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
            self.obj_layout.insertWidget(self.obj_layout.count()-2, widget_i)
        else:
            self.obj_layout.addWidget(widget_i)
        #return nummber_w, icon_w, name_label, chname_label, exe_edit, folder_button
    
    def _init_multi_line(self):
        for i in range(self.num):
            self._init_single_line(i, default=True)

    def _init_add_line(self):
        self.add_button = YohoPushButton(icon_i=self.add_button_icon, 
                                         style_config=self.add_button_style,
                                        )
        UIUpdater.set(self.line_height, self.add_button.setFixedHeight)
        self.add_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.add_button.clicked.connect(self._insert_line)
        self.add_button_lo = amlayoutH()
        UIUpdater.set(self.add_button_margin, self.add_button_lo.setContentsMargins, 'margin')
        add_obj(self.add_button, parent_f=self.add_button_lo)
    
    @abstractmethod
    def change_icon(self):
        pass
    @abstractmethod
    def name_edit_change(self):
        pass
    @abstractmethod
    def _change_icon(self):
        pass
    @abstractmethod
    def _exe_search(self):
        pass
class LauncherSetting(UILauncherSetting):
    def __init__(self, config:Config_Manager, parent:QMainWindow, manager:LauncherPathManager):
        super().__init__(config, parent , manager)
    
    def _writein_data(self, index_f:int):
        name_l = []
        chname_l = []
        exe_l = []
        icon_l = []
        for i in range(self.line_num):
            name_i = self.objs_l[i]['name'].text()
            if not name_i or name_i in name_l:
                continue
            chname_i = self.objs_l[i]['chname'].text()
            exe_i = self.objs_l[i]['exe'].text()
            icon_i = self.objs_l[i]['icon'].property('icon_path')
            name_l.append(name_i)
            chname_l.append(chname_i)
            exe_l.append(exe_i)
            icon_l.append(icon_i)
        df_data = [{'Name':name_l[i], 'Chinese Name':chname_l[i], 'EXE Path':exe_l[i], 'IconID':icon_l[i]} for i in range(len(name_l))]
        self.df_l[index_f][1] = pandas.DataFrame(df_data)

    def _line_fresh(self, index_f:int):
        self.line_num = 0
        self.df_n = self.df_l[index_f][1]
        for i in range(self.df_n.shape[0]):
            if i >= self.num:
                self._insert_line()
            self.widget_l[i].setVisible(True)
            self.objs_l[i]['number'].setText(str(i))
            self.objs_l[i]['name'].setText(self.df_n.iloc[i, 0])
            self.objs_l[i]['chname'].setText(self.df_n.iloc[i, 1])
            self.objs_l[i]['exe'].setText(self.df_n.iloc[i, 3])
            icon_c = self.df_n.iloc[i].loc['IconID']
            if icon_c:
                print(icon_c)
                self.objs_l[i]['icon'].setIcon(QIcon(self.df_n.iloc[i, -1]))
            else:
                icon_d = self.manager.get_app_icon(self.df_n.iloc[i, 0], self.df_l[index_f][0])
                if isinstance(icon_d, atuple):
                    icon_d = self.config.get(icon_d,'')
                self.objs_l[i]['icon'].setIcon(AIcon(icon_d))
            self.line_num += 1
        for i in range(len(self.widget_l)):
            if i >= self.df_n.shape[0]:
                self.widget_l[i].setVisible(False)
    
    def _init_bottom_control(self):
        self.bottom_layout = amlayoutH('c', spacing=25)
        self.tab_wdiget = QWidget()
        self.tab_layout = amlayoutH('l', spacing=10)
        self.tab_wdiget.setLayout(self.tab_layout)
        self.tab_bar = SheetControl(parent=self, font_f=self.tab_font, style_main=self.tab_style, style_menu=self.meunu_style)
        
        for name_i in [i[0] for i in self.df_l]:
            self.tab_bar.addTab(name_i)
        
        self.tab_bar.currentChanged.connect(self.change_tab)
        self.tab_bar.setCurrentIndex(0)
        self.b_add_button = YohoPushButton(icon_i=self.add_sheet_button_icon, style_config=self.tab_add_style, size_f=self.tab_height)
        self.b_add_button.clicked.connect(self.add_tab)
        self.tab_layout.addWidget(self.tab_bar)
        add_obj(self.b_add_button, parent_f=self.tab_layout)
        
        self.save_button = YohoPushButton(text_f='Save', font_f=self.save_button_font, style_config=self.save_button_style, size_f=self.line_height)
        self.save_button.clicked.connect(self._save)
        self.reset_button = YohoPushButton(text_f='Reset', font_f=self.reset_button_font, style_config=self.reset_button_style, size_f=self.line_height)
        self.reset_button.clicked.connect(self._reset)
        # self.discard_button = ChangeControl('Discard', self.config.get('discard_button', obj='color'), self.config.get('discard_button', obj='font'), self.line_height)
        # self.discard_button.clicked.connect(self._discard)
        UIUpdater.set(self.bottom_margin, self.bottom_layout.setContentsMargins, 'margin')
        self.bottom_layout.addWidget(self.tab_wdiget)
        self.bottom_layout.addStretch()
        add_obj(self.save_button, self.reset_button, parent_f=self.bottom_layout)
        
    def _insert_line(self):
        page_text = self.tab_bar.get_current_text()
        index_f = [i for i, j in enumerate(self.df_l) if j[0]==page_text]
        if not index_f:
            return
        page_index = index_f[0]
        #self.df_n.loc[len(self.df_n)] = ['', '', '', '', page_text, None]
        if self.line_num >= len(self.widget_l):
            self._init_single_line(self.line_num, default=True, insert=True)
        else:
            self.widget_l[self.line_num].setVisible(True)
            self.objs_l[self.line_num]['number'].setText(str(self.line_num))
            self.objs_l[self.line_num]['name'].setText('')
            self.objs_l[self.line_num]['chname'].setText('')
            self.objs_l[self.line_num]['exe'].setText('')
            self.objs_l[self.line_num]['icon'].setIcon(AIcon(self.config[self.default_app_icon]))
        self.line_num += 1
        self.sroll_down()
    
    def sroll_down(self):
        self.scroll_content.updateGeometry()
        self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum()+96)

    def add_tab(self, name='new_sheet', refresh:bool=True):
        text_l = self.tab_bar.get_texts()
        for i in range(99):
            name_t = f'{name}_{i}'
            if name_t not in text_l:
                break
        self.tab_bar.addTab(name_t)
        self.df_l.append([name_t, self._get_default_df(name_t)])
        if refresh:
            self.tab_bar.set_current_tab(name_t)
    
    def change_tab(self, index_new:int):
        self._writein_data(self.tab_index)
        self.tab_index = index_new
        self._line_fresh(index_new)

    def rename_tab(self, index):
        current_name = self.tab_bar.tabText(index)
        new_name, ok = QInputDialog.getText(self, "Rename Sheet", "Enter New Name:", text=current_name)
        if ok and new_name.strip():
            if new_name in self.tab_bar.get_texts():
                self.up.tip('Warning', 'Name already exists', {'OK':False}, False)
                return
            self.tab_bar.setTabText(index, new_name)
            self.df_l[index][0] = new_name
    
    def delete_tab(self, index):
        tip_prompt = f'Are you sure to DELETE sheet "{self.tab_bar.tabText(index)}"?'
        out_f = self.up.tip('Warning', tip_prompt, {'Yes':True, 'No':False}, False)
        if out_f:
            self.tab_bar.removeTab(index)
            self.df_l.pop(index)
    
    def sort_tab(self):
        tab_text_l = self.tab_bar.get_texts()
        index_i = self.tab_bar.currentIndex()
        df_l = []
        for i in tab_text_l:
            for j in self.df_l:
                if j[0] == i:
                    df_l.append(j)
        self.df_l = df_l
        self.tab_index = index_i

    def _change_icon(self, index_f:int):
        file_filter = "Images (*.svg *.png *.jpg *.jpeg *.ico)"
        file_path, _ = QFileDialog.getOpenFileName(self, "Select an image", "", file_filter)
        if not file_path:
            return
        icon_i = QIcon(file_path)
        self.objs_l[index_f]['icon'].setIcon(icon_i)
        self.objs_l[index_f]['icon'].setProperty('icon_path', file_path)
        # _, ext = os.path.splitext(file_path)
        # id_l = self.df_n.loc[:,'IconID'].to_list()
        # name = self.objs_l[index_f]['name'].text()
        # id_ls = [i.split('.')[0] for i in id_l if i]
        # if name in id_ls:
        #     for path_i in glob(os.path.join(self.tmp_icon_folder, f'{name}.*')):
        #         os.remove(path_i)
        
        # self.df_n.loc[index_f, 'IconID'] = f'{name}{ext}'
        # dst = os.path.join(self.tmp_icon_folder, f'{name}{ext}')
        # shutil.copy(file_path, dst)
    
    def name_edit_change(self):
        edit_f = self.sender()
        text = edit_f.text()
        # index_f = edit_f.property('index')
        type_f = edit_f.property('type')
        # if type_f == 'name':
        #     self.df_n.iloc[index_f, 0] = text
        # else:
        #     self.df_n.iloc[index_f, 1] = text
        # if type_f == 'name':
        #     names = self.df_n.loc[:,'Name'].to_list()
        # else:
        #     names = self.df_n.loc[:,'Chinese Name'].to_list()
        names = [i['name'].text() for i in self.objs_l.values()]
        if names.count(text) > 1:
            if type_f == 'name':
                edit_f._setStlye(False)
            else:
                pass
        else:
            edit_f._setStlye(True)

    def _exe_search(self, index_f:int):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Open File", "",
                                                  "All Files (*);;Python Files (*.py)", options=options)
        if file_name:
            file_name = file_name.replace('/', '\\')
            self.objs_l[index_f]['exe'].setText(file_name)
    
    def _reset(self):
        title_f = 'Warning'
        prompt_f = 'Are you sure to reset pages to last stage?'
        value_d = {'Reset All':2, "Reset This Page":1, 'Cancel':-5}
        out_f = self.up.tip(title_f, prompt_f, value_d, -5)
        page_n = self.tab_bar.get_current_text()
        page_index = self.tab_bar.currentIndex()
        match out_f:
            case 1:
                if page_n not in self.df.keys():
                    self.df_l[page_index][1] = self._get_default_df(page_n)
                else:
                    self.df_l[page_index][1] = self.df[page_n].copy(deep=True)
                    self.df_l[page_index][1].loc[:,'IconID'] = None
                self._line_fresh(page_index)
            case 2:
                self._process_ori_df()
                self._line_fresh(page_index)

    def _save(self):
        title_f = 'Warning'
        prompt_f = 'Are you sure to write in pages to local data?'
        value_d = {'Save All':2, "Save This Page":1, 'Cancel':-5}
        out_f = self.up.tip(title_f, prompt_f, value_d, -5)
        page_n = self.tab_bar.get_current_text()
        page_index = self.tab_bar.currentIndex()
        page_names = [i[0] for i in self.df_l]
        ori_pages = self.df.keys()
        match out_f:
            case 1:
                self._writein_data(page_index)
                df_toadd = self.df_l[page_index][1].drop('IconID', axis=1)
                self.df[page_n] = df_toadd
                self.df = OrderedDict([[key, self.df[key]] for key in page_names if key in ori_pages])
                self.manager.save_xlsx()
            case 2:
                self._writein_data(page_index)
                df_to_write = OrderedDict()
                for name, df in self.df_l:
                    df_to_write[name] = df.drop('IconID', axis=1, inplace=False)
                self.df = df_to_write
                self.manager.save_xlsx()
            case _:
                return


