from ..tools.toolbox import *
from Scripts.manager.paths_transfer import *
from PySide2.QtWidgets import  QMainWindow, QWidget
from PySide2.QtGui import QFontMetrics
from PySide2.QtCore import Qt
from Scripts.ui.custom_widget import *
from typing import Literal

class SwitchButton2(QComboBox):
    def __init__(self, parent: QMainWindow, config:Config_Manager) -> None:
        super().__init__(parent)
        self.up = parent
        self.name = "switch_button"
        self.config = config.deepcopy()
        self.config.group_chose(mode="MainWindow", widget=self.name)
        self.mode_list = self.config.get("mode_list", mode="Common", widget=None, obj=None)
        self.currentIndexChanged.connect(self._index_change)  
        self.font_f = atuple('MainWindow', self.name, 'font')
        self.height_f = atuple('MainWindow', self.name, 'Size', 'height')
        self.style_config = atuple('MainWindow', self.name, 'style')
        UIUpdater.set(self.style_config, self.customStyle)
        UIUpdater.set(alist(self.font_f, self.height_f), self._loadconfig, 
                      alist('font', None))
        self._initUI()

    def customStyle(self, config:dict):
        box_config:dict = config.get('box', {})
        menu_config:dict = config.get('menu', {})
        b_bg = box_config.get('background', 'rgba(255, 255, 255, 50)')
        b_font_color = box_config.get('font_color', '#F7F7F7')
        b_border = box_config.get('border', 'none')
        b_radius = box_config.get('border_radius', 10)
        b_padding = box_config.get('padding', [5,0,5,5])

        m_font_color = menu_config.get('font_color', '#F7F7F7')
        m_bg = menu_config.get('background', '#9DCDC8FF')
        m_hover_bg = menu_config.get('line_hover_background', '#4CC1B5')
        m_hover_font_color = menu_config.get('hover_font_color', 'black')

        self.style_d = {
            "QComboBox": {
                "background": b_bg,
                "color": b_font_color,
                "border": b_border,
                "border-radius": f"{b_radius}px",
                "padding": f"{b_padding[2]}px {b_padding[1]}px {b_padding[3]}px {b_padding[0]}px"
            },
            "QComboBox::drop-down": {
                "border": "none"
            },
            "QComboBox QAbstractItemView": {
                "padding": f"{b_padding[2]}px {b_padding[1]}px {b_padding[3]}px {b_padding[0]}px",
                'border': 'none',
                "background-color": m_bg,
                "color": m_font_color,
                "selection-background-color": m_hover_bg,
                "selection-color": m_hover_font_color
            },
            "QComboBox QAbstractItemView::item": {
                            "border": "none",
                            "border-style": "none",
                            "outline": "none",
                            "box-shadow": "none"
                        },
            "QComboBox QAbstractItemView::item:hover": {
                "border": "none",
                "border-style": "none",
                "outline": "none",
                "box-shadow": "none",
                "background-color": m_hover_bg,
                "color": m_hover_font_color
            },
            "QComboBox QAbstractItemView::item:selected": {
                "border": "none", 
                "border-style": "none",
                "outline": "none",
                "box-shadow": "none",
                "background-color": m_hover_bg,
                "color": m_hover_font_color
            }
        }
        self.style_sheet = style_make(self.style_d)
        self.setStyleSheet(self.style_sheet)

    def _loadconfig(self, font_f, height_f):
        self.setFixedHeight(height_f)
        self.setFont(font_f)

    def _initUI(self):
        for model_if in self.mode_list:
            self.addItem(model_if)
        self.setCurrentIndex(0)

        font_metrics = QFontMetrics(self.font())
        min_length = font_metrics.boundingRect('Local').width() + 30  
        length_t = font_metrics.boundingRect(self.mode_list[0]).width() + 30
        length_t = max(length_t, min_length)
        self.setFixedWidth(length_t)
    
    def _index_change(self):
        mode_n = self.currentText()
        font_metrics = QFontMetrics(self.font())
        min_length = font_metrics.boundingRect('Local').width() + 30  
        w_f = max(font_metrics.boundingRect(mode_n).width() + 30  ,min_length)  
        self.setFixedWidth(w_f)

class SwitchButton(CustomComboBox):
    def __init__(self, parent: QMainWindow, config:Config_Manager) -> None:
        self.name = "switch_button"
        self.config = config.deepcopy()
        self._load()
        super().__init__(modes=self.modes, style_d=self.style_d, box_height=self.box_h, 
                         box_font=self.box_font, menu_font=self.menu_font, parent=parent)
            
    def _index_change(self):
        mode_n = self.currentText()
        font_metrics = QFontMetrics(self.font())
        min_length = font_metrics.boundingRect('Local').width() + 30  
        w_f = max(font_metrics.boundingRect(mode_n).width() + 30  ,min_length)  
        self.setFixedWidth(w_f)

    def _load(self):
        self.pre = atuple('MainWindow', self.name)
        self.menu_font = self.pre|atuple('font', 'menu')
        self.box_font = self.pre|atuple('font', 'box')
        self.box_h = self.pre|atuple('Size', 'box_height')
        self.style_d = self.pre|atuple('style')
        self.modes = self.config[atuple('Common', 'mode_list')]

class TopButton(QWidget, QObject):
    button_click = Signal(str)  # Literal['minimum', 'maximum', 'close']
    def __init__(self, parent: QMainWindow, config:Config_Manager) -> None:
        super().__init__(parent)
        self.name = "top_button"
        self.up = parent
        self.config = config.deepcopy()
        self.config.group_chose(mode="MainWindow", widget=self.name)
        self.geom = atuple('MainWindow', self.name, 'Size', 'widget_height')
        UIUpdater.set(self.geom, self.setFixedHeight)
        self.max_state = False
        
    def _initbuttons(self):
        self.pre = atuple('MainWindow', self.name)
        size_i = atuple('MainWindow', self.name, 'Size', 'button_size')
        pre = ['MainWindow', self.name, 'path']
        self.max_path = atuple(pre+['maximum'])
        self.min_path = atuple(pre+['minimum'])
        self.middle_path = atuple(pre+['middle'])
        self.close_path = atuple(pre+['close'])
        self.entry_path = atuple(pre+['entry'])
        style_f = self.pre|atuple('style')

        self.max_button = YohoPushButton(icon_i=self.max_path, style_config=style_f, size_f=size_i)
        self.max_button.clicked.connect(lambda: self._b_click('maximum'))
        self.min_button = YohoPushButton(icon_i=self.min_path, style_config=style_f, size_f=size_i)
        self.min_button.clicked.connect(lambda: self._b_click('minimum'))
        self.close_button = YohoPushButton(icon_i=self.close_path, style_config=style_f, size_f=size_i)
        self.close_button.clicked.connect(lambda: self._b_click('close'))

        self.enty_button = YohoPushButton(icon_i=self.entry_path, style_config=style_f, size_f=size_i)
        self.enty_button.clicked.connect(lambda: self._b_click('entry'))

        return [self.enty_button, self.min_button, self.max_button, self.close_button]

    def _b_click(self, sign:Literal['minimum', 'maximum', 'close', 'entry']):
        self.button_click.emit(sign)

    @Slot(str)
    def _isMax(self, state:bool):
        if state:
            self.max_button.setIcon(self.max_path)
        else:
            self.max_button.setIcon(self.middle_path)

class InfoTip(QDialog):
    def __init__(self,
                 type_f:Literal['Info', 'Warning', 'Error'], 
                 prompt_f:str, 
                 buttons:dict[str,str|dict[Literal['colors', 'value',],bool|str|str]],
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
        UIUpdater.set(atuple('MainWindow', 'Tip', 'color', 'background'), self._setStyle)
    @classmethod
    def _load_config(cls, config:Config_Manager):
        cls.config = config.deepcopy()
    
    def _load(self):
        pre = ['MainWindow', 'Tip', 'font']
        self.title_font = atuple(pre+['title'])
        self.prompt_font = atuple(pre+['prompt'])
        self.button_font = atuple(pre+['button'])

        pre = ['MainWindow', 'Tip', 'Size']
        self.button_margin = atuple(pre+['button_margin'])
        self.prompt_margin = atuple(pre+['prompt_margin'])
        self.title_height = atuple(pre+['title_height'])
        self.button_size = atuple(pre+['button_size'])
        self.widget_size = atuple(pre+['widget_size'])

        self.button_colors = atuple('MainWindow', 'Tip', 'color', 'button')
        self.info_icon = atuple('MainWindow', 'Tip', 'path', 'info_icon')
        self.warning_icon = atuple('MainWindow', 'Tip', 'path', 'warning_icon')
        self.error_icon = atuple('MainWindow', 'Tip', 'path', 'error_icon')

    def _init_ui(self):
        self.layout0 = amlayoutV()
        self.setLayout(self.layout0)
        self.layout_tile = amlayoutH(spacing=15)
        self.layout_prompt = amlayoutH()
        UIUpdater.set(self.prompt_margin, self.layout_prompt.setContentsMargins,type_f='margin')

        self.layout_button = amlayoutH()
        UIUpdater.set(self.button_margin, self.layout_button.setContentsMargins, type_f='margin')
        UIUpdater.set(self.title_font, self.setFont, 'font')
        
        self.title_icon = AutoLabel(text='', icon_f=self.title_icon,width=self.title_height, height=self.title_height)
        self.title_icon.setAlignment(Qt.AlignCenter)

        self.title_name = AutoLabel(text=self.type, font=self.title_font)
        self.title_name.setAlignment(Qt.AlignLeft)
        add_obj(self.title_icon, self.title_name, parent_f=self.layout_tile)
        
        self.promt_label = AutoLabel(text=self.prompt, font=self.prompt_font)
        self.promt_label.setWordWrap(True)
        self.promt_label.setAlignment(Qt.AlignCenter)
        self.layout_prompt.addWidget(self.promt_label)

        for name, value in self.buttons.items():
            button_i  = ColorfulButton(name, self.button_colors, self.title_font)
            button_i.setProperty('value', value)
            UIUpdater.set(self.button_size, button_i.setFixedSize, 'size')
            self.layout_button.addWidget(button_i)
            button_i.clicked.connect(self._return)
        
        add_obj(self.layout_tile, self.layout_prompt, self.layout_button, parent_f=self.layout0)
        UIUpdater.set(self.widget_size, self.setFixedSize, 'size')
    
    def _setStyle(self, background_color):
        style_sheet = f'''
            QWidget {{
                background-color: {background_color};
                border-radius: 10px;
            }}
        '''
        self.setStyleSheet(style_sheet)
    
    def _return(self):
        button = self.sender()
        self.VALUE = button.property('value')
        super().accept()

