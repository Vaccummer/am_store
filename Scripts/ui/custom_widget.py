from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
import random
from functools import partial
from Scripts.manager.config_ui import *
from typing import Literal, Optional, Tuple, Union, List
from abc import abstractmethod
from Scripts.manager.paths_transfer import *

class YohoPushButton(QPushButton):
    def __init__(self, style_config:atuple,
                 icon_i:Union[str, AIcon, Tuple]='',
                 text_f:str='',
                 font_f:QFont=None,
                 size_f:Union[int, QSize, Tuple]=None, 
                 height_f:int=None,
                 width_f:int=None,
                 an_time:int=180,
                 change_size:float=0.5,
                 change_period:float=0.7,
                 icon_proportion:float=0.95,
                 parent=None):
        if parent is None:
            super().__init__()
        else:
            super().__init__(parent)
        self.setText(text_f)
        self.an_type = "resize"
        self.an_time = an_time
        self.default_an_time = an_time
        self.extra_style_dict = {}
        UIUpdater.set(font_f, self.setFont, type_f='font')
        UIUpdater.set(icon_proportion, self._loadIconProportion)
        self.style_ctl = UIUpdater.set(style_config, self.customStyle, 'style')
        # 设置按钮图标
        if icon_i is not None:
            UIUpdater.set(icon_i, self.setIcon, type_f='icon')
        if size_f is not None:
            UIUpdater.set(size_f, self.setFixedSize, type_f='size')
        if height_f is not None:
            UIUpdater.set(height_f, self.setFixedHeight, type_f='height')
        if width_f is not None:
            UIUpdater.set(width_f, self.setFixedWidth, type_f='width')
        self.change_size = change_size
        self.change_period = change_period
        self.clicked.connect(self.start_animation)
    
    def start_animation(self):
        if self.an_type == "shake":
            self.shake_icon()
        elif self.an_type == "resize":
            self.resize_icon()
    
    def shake_icon(self):
        self.animation = QPropertyAnimation(self, b"geometry")
        start_rect = self.geometry()
        self.animation.setDuration(self.an_time)
        self.animation.setStartValue(QRect(start_rect))
        self.animation.setKeyValueAt(0.2, QRect(start_rect.x() - 5, start_rect.y(), start_rect.width(), start_rect.height()))
        self.animation.setKeyValueAt(0.4, QRect(start_rect.x() + 5, start_rect.y(), start_rect.width(), start_rect.height()))
        self.animation.setKeyValueAt(0.6, QRect(start_rect.x() - 5, start_rect.y(), start_rect.width(), start_rect.height()))
        self.animation.setKeyValueAt(0.8, QRect(start_rect.x() + 5, start_rect.y(), start_rect.width(), start_rect.height()))
        self.animation.setEndValue(QRect(start_rect))
        self.animation.start()
    
    def resize_icon(self):
        self.animation = QPropertyAnimation(self, b"iconSize")
        self.animation.setDuration(self.an_time)
        size_n = self.iconSize()
        size_t = QSize(int(self.change_size*size_n.width()), int(self.change_size*size_n.height()))
        self.animation.setStartValue(size_n)
        self.animation.setKeyValueAt(self.change_period, size_t)  
        self.animation.setEndValue(size_n)  
        self.animation.start()

    def _loadIconProportion(self,icon_proportion:float):
        self.icon_proportion = icon_proportion
        self._resize(self.size())

    def resizeEvent(self, event):
        # automatically resize the icon to fit the button size
        super().resizeEvent(event)
        new_size = self.size()
        w, h = new_size.width(), new_size.height()
        rf = min(w, h)
        self.setIconSize(QSize(int(rf*self.icon_proportion), int(rf*self.icon_proportion)))
    
    def _resize(self, size_f:Union[int, QSize, list]):
        if isinstance(self.icon_proportion, float):
            res_factor = self.icon_proportion
        elif isinstance(self.icon_proportion, atuple):
            res_factor = UIUpdater.get(self.icon_proportion, 0.9)
        else:
            res_factor = 0.9
        if isinstance(size_f, int):
            size_f = QSize(size_f, size_f)
        elif isinstance(size_f, list):
            size_f = QSize(size_f[0], size_f[1])
        self.size_f = size_f
        self.setFixedSize(size_f)
        self.setIconSize(QSize(int(size_f.width()*res_factor), int(size_f.height()*res_factor)))

    def customStyle(self, format_dict:dict, escape_sign:dict={}):
        self.an_type = format_dict.get('animation_type', None)
        self.an_time = format_dict.get('animation_time', self.default_an_time)
        if not isinstance(self.an_time, int):
            self.an_time = self.default_an_time
        
        bg_colors = Udata(atuple('background_colors'), ["rgba(255,255,255,80)", "rgba(255,255,255,180)", "rgba(255,255,255,240)"])
        border_radius = Udata(atuple('border_radius'), 10)
        border = Udata(atuple('border'), 'none')
        padding = Udata(atuple('padding'), [0,0,0,0])
        temp_dict = {
            'QPushButton': {
                'background-color': bg_colors[0],
                'border': border,
                'padding': padding,
                'border-top-left-radius': border_radius[0],
                'border-top-right-radius': border_radius[1],
                'border-bottom-right-radius': border_radius[2],
                'border-bottom-left-radius': border_radius[3],
            },
            'QPushButton:hover': {
                'background-color': bg_colors[1],
            },
            'QPushButton:pressed': {
                'background-color': bg_colors[2],
            }
        }
        if not hasattr(self, 'style_dict'):
            self.style_dict = {}
        self.style_dict = process_style_dict(self.style_dict, temp_dict, escape_sign, format_dict)
        self.setStyleSheet(style_make(self.style_dict|self.extra_style_dict))

class ColorfulButton(QPushButton):
    def __init__(self, text_f:str, colors:list[str], font:QFont, height:int=None, width:int=None):
        super().__init__()
        self.setText(text_f)
        UIUpdater.set(font, self.setFont, type_f='font')
        UIUpdater.set(height, self.setFixedHeight)
        UIUpdater.set(width, self.setFixedWidth)
        self._setstyle(colors)
    
    def _setstyle(self, colors):
        style_sheet = f'''
        QPushButton {{
            background-color: {colors[0]};
            border-radius: 10px;
            padding: 10px;
        }}
        QPushButton:hover {{
            background-color: {colors[1]};
        }}
        QPushButton:pressed {{
            background-color: {colors[2]};
        }}
        '''
        self.setStyleSheet(style_sheet)

class AutoLabel(QLabel):
    def __init__(self, text:str, font:Union[QFont,atuple], style_config:atuple, icon_f:Union[str,atuple,QIcon]=None, 
                 height=None, width=None):
        super().__init__()
        if isinstance(text, str):
            self.setText(text)
        else:
            UIUpdater.set(text, self.setText)
        UIUpdater.set(height, self.setFixedHeight, type_f='height')
        UIUpdater.set(width, self.setFixedWidth, type_f='width')
        UIUpdater.set(font, self.setFont, type_f='font')
        UIUpdater.set(icon_f, self.set_icon, type_f='icon')
        UIUpdater.set(style_config, self.customStyle, 'style')
        self.setAlignment(Qt.AlignCenter)
    
    def customStyle(self, format_dict:dict, escape_sign:dict={}):
        bg_color = Udata(atuple('background_colors'), ['transparent', 'transparent', 'transparent'])
        border_radius = Udata(atuple('border_radius'), 10)
        border = Udata(atuple('border'), 'none')
        padding = Udata(atuple('padding'), [5,5,5,5])
        text_align = Udata(atuple('text_align'), 'left')
        temp_dict = {
            'QLabel': {
                'background-color': bg_color,
                'border-top-left-radius': border_radius,
                'border-top-right-radius': border_radius,
                'border-bottom-right-radius': border_radius,
                'border-bottom-left-radius': border_radius,
                'border': border,
                'padding': padding,
                'text-align': text_align,
            },
            'QLabel::hover': {
                'background-color': bg_color[1],
            },
            'QLabel::pressed': {
                'background-color': bg_color[2],
            }
        }
        if not hasattr(self, 'style_dict'):
            self.style_dict = {}
        self.style_dict = process_style_dict(self.style_dict, temp_dict, escape_sign, format_dict)
        self.setStyleSheet(style_make(self.style_dict))

    # def set_text(self, text:str):
    #     self.setText(text)
    #     self.adjustSize()
    
    # def set_color(self, color:str, border_radius:int=5):
    #     sheet_f = f'''
    #                 QLabel {{
    #                         border-radius: {border_radius}px;  /* 边角弧度 */
    #                         padding-left: 5px;   /* 左边距 */
    #                         padding-right: 5px;  /* 右边距 */
    #                         padding-top: 0px;    /* 上边距 */
    #                         padding-bottom: 0px; /* 下边距 */
    #                         background-color: {color};  /* 背景透明 */
    #                         text-align: center;  /* 文字居中 */
    #                         }}
    #                 '''
    #     self.setStyleSheet(sheet_f)

    def set_icon(self, icon:Union[str,QIcon]):
        if isinstance(icon, str):
            self.setPixmap(QPixmap(icon))
        elif isinstance(icon, QIcon):
            self.setPixmap(icon.pixmap(-1,-1))

class AutoEdit(QLineEdit):
    def __init__(self, text='', font:atuple=None, style_d={}, height:atuple=None, width:atuple=None, disable_scroll:bool=True):
        super().__init__()
        self.scroll_step = 10  # 基础滚动步长
        self.scroll_acceleration = 1.5  # 滚动加速度
        self.max_scroll_step = 30  # 最大滚动步长
        self.disable_scroll = disable_scroll
        # 平滑滚动
        self.scroll_timer = QTimer(self)
        self.scroll_timer.timeout.connect(self._smooth_scroll)
        self.target_position = 0
        self.current_velocity = 0
        self.setText(text)
        UIUpdater.set(font, self.setFont, type_f='font')
        UIUpdater.set(height, self.setFixedHeight)
        if width is not None:
            UIUpdater.set(width, self.setFixedWidth)
        UIUpdater.set(style_d, self.customStyle, 'style')
        self.cursor_paint_time = 0

    def customStyle(self, style_dict:dict, escape_sign:dict={}):
        bg_color = Udata(atuple('background'), 'white')
        font_color = Udata(atuple('font_color'), 'black')
        border_radius = Udata(atuple('border_radius'), 10)
        border = Udata(atuple('border'), 'none')
        padding = Udata(atuple('padding'), [10,0,5,5])
        text_selected_color = Udata(atuple('text_selected_color'), '#2471A3')
        text_selected_font_color = Udata(atuple('text_selected_font_color'), None)
        placeholder_style = Udata(atuple('placeholder_font_style'), 'normal')
        placeholder_color = Udata(atuple('placeholder_color'), 'gray')
        temp_dict = {
            'QLineEdit': {
                'background-color': bg_color,
                'color': font_color,
                'border-top-left-radius': border_radius[0],
                'border-top-right-radius': border_radius[1],
                'border-bottom-right-radius': border_radius[2],
                'border-bottom-left-radius': border_radius[3],
                'border': border,
                'padding-left': padding[0],
                'padding-top': padding[1],
                'padding-right': padding[2],
                'padding-bottom': padding[3],
                'selection-background-color': text_selected_color,
                'selection-color': text_selected_font_color,
            },
            "QLineEdit::placeholder": {
                'color': placeholder_color,
                'font-style': placeholder_style,
            }
        }
        if not hasattr(self, 'style_dict'):
            self.style_dict = {}
        self.style_dict = process_style_dict(self.style_dict, temp_dict, escape_sign, style_dict)
        self.setStyleSheet(style_make(self.style_dict))
    
    def wheelEvent(self, event: QWheelEvent):
        if self.disable_scroll:
            super().wheelEvent(event)
            return
        text_width = self.fontMetrics().width(self.text())
        visible_width = self.width() - self.textMargins().left() - self.textMargins().right()
        if text_width <= visible_width:
            super().wheelEvent(event)
            return
        delta = event.angleDelta().y()
        scroll_amount = self.scroll_step * (1 if delta < 0 else -1)
        current_pos = self.cursorPosition()
        self.target_position = max(0, min(len(self.text()), 
                                        current_pos + scroll_amount))
        
        if not self.scroll_timer.isActive():
            self.scroll_timer.start(16)  
        event.accept()
    
    def _smooth_scroll(self):
        current_pos = self.cursorPosition()
    
        if current_pos == self.target_position:
            self.scroll_timer.stop()
            self.current_velocity = 0
            return
            
        # 计算新位置
        direction = 1 if self.target_position > current_pos else -1
        self.current_velocity = min(self.max_scroll_step, 
                                  abs(self.current_velocity + self.scroll_acceleration)) * direction
        
        new_pos = int(current_pos + self.current_velocity)
        new_pos = max(0, min(len(self.text()), new_pos))
        
        # 更新位置
        self.setCursorPosition(new_pos)
        
        # 如果接近目标位置，直接设置到目标位置
        if abs(new_pos - self.target_position) < abs(self.current_velocity):
            self.setCursorPosition(self.target_position)
            self.scroll_timer.stop()
            self.current_velocity = 0
            
    def setText(self, text: str):
        super().setText(text)
        self.setCursorPosition(0)  

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.hasFocus():
            self.cursor_paint_time +=1
            if self.cursor_paint_time % 2 == 0:
                color = '#943126' 
            else:
                color = 'transparent'
            painter = QPainter(self)
            rect = self.cursorRect()
            painter.fillRect(
                QRect(rect.x(), rect.y(), 5, rect.height()),
                color
            )

class WheelEdit(AutoEdit):
    wheel_signal = Signal(int)
    def __init__(self, text='', font:atuple=None, style_d={}, height:atuple=None, width:atuple=None):
        super().__init__(text=text, font=font, style_d=style_d, height=height, width=width)
        self.setReadOnly(True)
        self.setMouseTracking(True)
        self.setContextMenuPolicy(Qt.NoContextMenu)
    
    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.wheel_signal.emit(1)
        else:
            self.wheel_signal.emit(-1)

class ModeButton(YohoPushButton, QObject):
    textChanged = Signal(str)
    wheel_signal = Signal(int)
    def __init__(self, style_d, text_f='', font_f=None, height_f=None, color_state=0, parent=None):
        super().__init__(style_config=style_d, text_f=text_f, font_f=font_f, height_f=height_f)
        self.color_state = color_state
        UIUpdater.set(font_f, self.setFont, type_f='font')
        self.textChanged.connect(self._AutoResize)
        self.setText(text_f)
        UIUpdater.set(height_f, self.setFixedHeight, type_f='height')
        self.style_ctl:UIData = UIUpdater.set(style_d, self.customStyle, 'style')
        self.style_ctl.force_escape_sign = {atuple('background_colors'):True}

    def setText(self, text_f:str):
        super().setText(text_f)
        self.textChanged.emit(text_f)
    
    @Slot(str)
    def _AutoResize(self, text_f:str):
        size_ori = self.sizeHint().width() + 30
        self.setFixedWidth(size_ori)
    
    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.wheel_signal.emit(-1)
        else:
            self.wheel_signal.emit(1)

    def setBackgoundColors(self, colors:str|list[str]|atuple):
        if isinstance(colors, atuple):
            colors = UIUpdater.get(colors, default_v=None)
            if not colors:
                return
        colors = enlarge_list(colors, 3)
        self.style_dict['QPushButton']['background-color'] = colors[0]
        self.style_dict['QPushButton::hover']['background-color'] = colors[1]
        self.style_dict['QPushButton::pressed']['background-color'] = colors[2]
        self.setStyleSheet(style_make(self.style_dict))

class ModeListWidget(QListWidget):
    def __init__(self, style_d, max_height=None, font_f=None, parent=None, color_state=0):
        self.color_state = color_state
        if parent is None:
            super().__init__()
        else:
            super().__init__(parent=parent)
        self.default_item_margin = 1
        self.deault_extra_height = 5
        self.deault_extra_width = 30
        self.setWindowFlags(Qt.FramelessWindowHint)  
        UIUpdater.set(style_d, self.customStyle, 'style')
        UIUpdater.set(max_height, self.setMaximumHeight, type_f='height')
        UIUpdater.set(font_f, self.setFont, type_f='font')

    def customStyle(self, style_d:dict, escape_sign:dict={}):
        '''
        self.color_state: decide color group to use
        mainly influence background and font color
        0: default, don't use color_state
        1: use background_colors_1 and font_colors_1
        2: use background_colors_2 and font_colors_2
        '''
    
        menu_border = Udata(atuple('menu', 'border'), 'none')
        menu_border_radius = Udata(atuple('menu', 'border_radius'), 10)
        menu_padding = Udata(atuple('menu', 'padding'), 5)
        menu_bg = Udata(atuple('menu', 'background'), 'rgba(255, 255, 255, 80)')
        

        self.extra_height = UIUpdater.get(atuple('item', 'extra_height'), self.deault_extra_height)
        self.extra_width = UIUpdater.get(atuple('item', 'extra_width'), self.deault_extra_width)
        item_margin = Udata(atuple('item', 'margin'), 1)
        bg_colors = Udata(atuple('item', 'background_colors'), ['#2C51C1', '#FFC300', '#FF5733'])
        font_colors = Udata(atuple('item', 'font_colors'), ['#000000', '#000000', '#000000'])
        border = Udata(atuple('item', 'border'), 'none')
        border_radius = Udata(atuple('item', 'border_radius'), 10)
        padding = Udata(atuple('item', 'padding'), [10, 5, 5, 5])

        temp_dict = {
            'QListWidget':{
                'background-color': menu_bg,
                'border': menu_border,
                'padding': menu_padding,
                'border-top-left-radius': menu_border_radius[0],
                'border-top-right-radius': menu_border_radius[1],
                'border-bottom-right-radius': menu_border_radius[2],
                'border-bottom-left-radius': menu_border_radius[3],
            },
            'QListWidget::item':{
                'background-color': bg_colors[0],
                'color': font_colors[0],
                'padding': padding,
                'margin': item_margin,
                'border': border,
                'border-top-left-radius': border_radius[0],
                'border-top-right-radius': border_radius[1],
                'border-bottom-right-radius': border_radius[2],
                'border-bottom-left-radius': border_radius[3],
            },
            'QListWidget::item:hover':{
                'background-color': bg_colors[1],
                'color': font_colors[1],
            },
            'QListWidget::item:selected':{
                'background-color': bg_colors[2],
                'color': font_colors[2],
            },
            'QListWidget::QScrollBar':{
                'border': 'none',
                'background': 'transparent',
                'height': '0px',
                'width': '0px',
            }
        }
        if not hasattr(self, 'style_dict'):
            self.style_dict = {}
        self.style_dict = process_style_dict(self.style_dict, temp_dict, escape_sign, style_d)
        self.setStyleSheet(style_make(self.style_dict))

    def get_size(self):
        str_l = [self.item(i).text() for i in range(self.count())]
        width_l = [self.fontMetrics().width(text) for text in str_l]
        width_n = max(width_l) + self.extra_width
        height_n = self.fontMetrics().height() *(1+self.count()) + self.extra_height
        return width_n, height_n
    
    def get_max_width(self):
        return self.get_size()[0]
    
    def get_max_height(self):
        return self.get_size()[1]
    
class CustomComboBox(QWidget, QObject):
    index_changed = Signal(int)
    def __init__(self, modes:list, style_d:dict, box_height=None, box_font=QFont(), menu_font=QFont(),
                 parent=None):
        super().__init__(parent)
        self.color_state = 0 
        self.up = parent
        self.modes = modes
        self.default_an_time = 300
        self.style_d = style_d
        self.box_height = box_height
        self.box_font = box_font
        self.menu_font = menu_font
        self.initUI()
        self.setStyleSheet('''background-color: transparent;''')
        
    def initUI(self):
        # Layout
        self.layout0 = QVBoxLayout(self)
        self.layout0.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout0) 

        # Create line edit for display
        self.box_w = ModeButton(self.style_d, text_f='', font_f=self.box_font, height_f=self.box_height, color_state=self.color_state)
        self.box_w.clicked.connect(self.show_menu)
        self.box_w.wheel_signal.connect(self.wheel_signal_receiver)


        # Create list widget for dropdown
        self.menu_w = ModeListWidget(style_d=self.style_d, font_f=self.menu_font, parent=self.up, color_state=self.color_state)
        self.menu_w.hide()
        for mode in self.modes:
            self.add_item(mode)
        # self.menu_w.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.menu_w.setFixedSize(*self.menu_w.get_size())


        # Connect signals
        self.menu_w.itemClicked.connect(self.menu_click)
        add_obj(self.box_w, parent_f=self.layout0)

    def add_item(self, text):
        self.menu_w.addItem(text)
        if not self.box_w.text():
            self.box_w.setText(text)

    def show_menu(self):
        if self.menu_w.isVisible():
            self.menu_w.hide()
            return
        box_g = self.box_w.geometry()
        uper_g = self.geometry()
        x_n = box_g.x() + uper_g.x()
        y_n = box_g.y() + uper_g.y() + self.box_w.height() - 5
        # pos = self.box_w.geometry()
        self.menu_w.setGeometry(
            x_n, 
            y_n,
            self.menu_w.width(),
            0
        )
        self.menu_w.show()
        self.menu_animation()
        
    def menu_animation(self):
        self.animation = QPropertyAnimation(self.menu_w, b"geometry")
        self.animation.setDuration(self.default_an_time)
        # width_n = self.menu_w.get_max_width()
        start_rect = QRect(self.menu_w.x(), self.menu_w.y(), self.menu_w.width(), 0)
        end_rect = QRect(self.menu_w.x(), self.menu_w.y(), self.menu_w.width(), self.menu_w.get_size()[1])
        self.animation.setStartValue(start_rect)
        self.animation.setEndValue(end_rect)
        self.animation.start()
        self.menu_w.raise_()

    def menu_click(self, item):
        if self.menu_w.isVisible():
            index = self.modes.index(item.text())
            self.setIndex(index)
            self.menu_w.hide()
            item.setSelected(False)


    def setFixedWidth(self, w):
        self.box_w.setFixedWidth(w)
        # self.menu_w.setFixedWidth(w)
        return super().setFixedWidth(w)

    def setIndex(self, index:int):
        index = max(0, min(index, len(self.modes)-1))
        if index == self.getIndex():
            return
        self.box_w.setText(self.modes[index])
        self.index_changed.emit(index)
    
    def getIndex(self):
        return self.modes.index(self.box_w.text())
    
    def getMode(self, index_f:int=None):
        if index_f is None:
            return self.box_w.text()
        else:
            return self.modes[index_f]
    
    def wheel_signal_receiver(self, sign:int):
        index_n = self.getIndex()
        index_n += sign
        self.setIndex(index_n)
    
    def setWidth(self, text_f:str):
        text_f = self.box_w.text()
        line_edit_font = self.box_w.font()
        font_metrics = QFontMetrics(line_edit_font)
        text_width = font_metrics.width(text_f) + 70
        self.setFixedWidth(text_width)

class PolygonWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_shapes()  # 初始化多边形和圆形
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_positions)
        self.timer.start(50)  # 每50毫秒更新一次位置

        # 每隔一段时间随机改变方向
        self.change_direction_timer = QTimer(self)
        self.change_direction_timer.timeout.connect(self.change_directions)
        self.change_direction_timer.start(2000)  # 每2秒改变一次方向

        # 添加模糊效果
        blur_effect = QGraphicsBlurEffect(self)
        blur_effect.setBlurRadius(100)
        self.setGraphicsEffect(blur_effect)

    def init_shapes(self):
        """初始化固定形状、颜色的多边形和圆形，以及它们的速度向量"""
        # 初始化多边形
        self.polygons = [
            {"polygon": QPolygonF([QPointF(0, 0), QPointF(600, 0), QPointF(600, 500), QPointF(0, 500)]), "color": QColor("#17AAAE")},
            {"polygon": QPolygonF([QPointF(10, 150), QPointF(200, 150), QPointF(175, 200)]), "color": QColor("#7015AE")},
            {"polygon": QPolygonF([QPointF(10, 250), QPointF(300, 250), QPointF(275, 300)]), "color": QColor("#C312A9")}
        ]

        # 初始化圆形（定义圆的圆心和半径）
        self.circles = [
            {"center": QPointF(50, 50), "radius": 40, "color": QColor("#FF5733")}
        ]

        # 初始位移量（所有形状的初始位移设为0）
        self.offsets = [QPointF(0, 0), QPointF(0, 0), QPointF(0, 0)]
        self.circle_offsets = [QPointF(0, 0)]  # 圆形的初始位移

        # 初始速度向量 (vx, vy) 均匀运动
        self.velocities = [
            QPointF(random.randint(-5, 5), random.randint(-5, 5)),
            QPointF(random.randint(-5, 5), random.randint(-5, 5)),
            QPointF(random.randint(-5, 5), random.randint(-5, 5))
        ]
        self.circle_velocities = [
            QPointF(random.randint(-5, 5), random.randint(-5, 5))
        ]  # 圆形的速度向量

    def change_directions(self):
        """每隔一定时间随机改变一次速度向量"""
        for i in range(len(self.velocities)):
            self.velocities[i] = QPointF(random.randint(-5, 5), random.randint(-5, 5))
        for i in range(len(self.circle_velocities)):
            self.circle_velocities[i] = QPointF(random.randint(-5, 5), random.randint(-5, 5))

    def update_positions(self):
        """更新多边形和圆的位置（均匀运动）"""
        # 更新多边形
        for i in range(len(self.polygons)):
            self.offsets[i] += self.velocities[i]
            # 判断边界，超出视野重置到中心
            translated_polygon = self.polygons[i]["polygon"].translated(self.offsets[i])
            centroid = self.calculate_centroid(translated_polygon)
            if self.is_out_of_bounds(centroid):
                window_center = QPointF(self.width() / 2, self.height() / 2)
                reset_offset = window_center - centroid
                self.offsets[i] += reset_offset  # 更新偏移量

        # 更新圆的位置
        for i in range(len(self.circles)):
            self.circle_offsets[i] += self.circle_velocities[i]
            center_with_offset = self.circles[i]["center"] + self.circle_offsets[i]
            if self.is_out_of_bounds(center_with_offset):
                window_center = QPointF(self.width() / 2, self.height() / 2)
                reset_offset = window_center - center_with_offset
                self.circle_offsets[i] += reset_offset  # 更新偏移量

        self.update()  # 触发窗口重绘

    def calculate_centroid(self, polygon):
        """计算多边形的重心"""
        x_coords = [point.x() for point in polygon]
        y_coords = [point.y() for point in polygon]
        centroid_x = sum(x_coords) / len(polygon)
        centroid_y = sum(y_coords) / len(polygon)
        return QPointF(centroid_x, centroid_y)

    def is_out_of_bounds(self, centroid):
        """判断重心或圆心是否超出窗口视野"""
        rect = self.rect()  # 获取窗口的矩形区域
        return not rect.contains(centroid.toPoint())  # 将 QPointF 转换为 QPoint

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 清除上一次的绘图（填充背景色）
        painter.fillRect(self.rect(), Qt.white)  # 使用白色背景清空之前的绘制内容
        
        # 绘制多边形（应用位移）
        for i, poly_data in enumerate(self.polygons):
            polygon = poly_data["polygon"]
            color = poly_data["color"]
            offset = self.offsets[i]
            translated_polygon = polygon.translated(offset)
            painter.setBrush(color)
            painter.drawPolygon(translated_polygon)

        # 绘制圆形（应用位移）
        for i, circle_data in enumerate(self.circles):
            center = circle_data["center"]
            radius = circle_data["radius"]
            color = circle_data["color"]
            offset = self.circle_offsets[i]
            painter.setBrush(color)
            painter.drawEllipse(center + offset, radius, radius)  # 绘制圆形

class ProgressBar2(QProgressBar):
    def __init__(self, parent:QMainWindow, max_value:float, 
                 height:int, 
                 background_color:str='#E0E0E0', 
                 color_gradient:List[str]=['#DF461CC1', '#069D40FF'],
                 position_gradient:List[float]=[0, 1],
                 show_text:bool=False):
        super().__init__(parent)
        self.max_value = max_value
        self.setRange(0, max_value)  
        self.setValue(0)  
        self.progress=0
        UIUpdater.set(alist(height, background_color, color_gradient, position_gradient), self.custom_ui, alist())
        self.setTextVisible(show_text)  
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(50)
    @abstractmethod
    def update_progress(self):
        pass
    
    def custom_ui(self, height_f, b_color, color_gradient, position_gradient):
        len_t = min(len(color_gradient), len(position_gradient))
        match len_t:
            case 2:
                color_g = f"qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: {position_gradient[0]} {color_gradient[0]}, stop: {position_gradient[1]} {color_gradient[1]})"
            case 3:
                color_g = f"qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: {position_gradient[0]} {color_gradient[0]}, stop: {position_gradient[1]} {color_gradient[1]}, stop: {position_gradient[2]} {color_gradient[2]})"
            case 4:
                color_g = f"qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: {position_gradient[0]} {color_gradient[0]}, stop: {position_gradient[1]} {color_gradient[1]}, stop: {position_gradient[2]} {color_gradient[2]}, stop: {position_gradient[3]} {color_gradient[3]})"
            case _:
                color_g = "qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #DF461CC1, stop: 1 #069D40FF)"
        self.setFixedHeight(height_f)
        self.border_radius = height_f // 2
        self.stylesheet = f'''
        QProgressBar {{
            border-radius: {self.border_radius}px;
            background-color: {b_color};
            border: 0px solid ;
        }}
        QProgressBar::chunk {{
            border-radius: {self.border_radius}px;
            background: {color_g};
        }}
        '''
        self.setStyleSheet(self.stylesheet)
class ProgressBar(QProgressBar):
    def __init__(self, parent:QMainWindow, 
                 style_d:dict,  
                 max_value:float=100, 
                 height:int=10, 
                 ):
        super().__init__(parent)
        self.max_value = max_value
        self.setRange(0, max_value)  
        self.setValue(0)  
        UIUpdater.set(height, self.setFixedHeight, 'height')
        UIUpdater.set(style_d, self.customStyle, 'style')
        self.setTextVisible(False)
        
    def update(self, value_add:int):
        self.setValue(self.value()+value_add)

    def customStyle(self, style_d:dict, escape_sign:dict={}):
        bg_color = Udata(atuple('background'), 'rgba(255, 255, 255, 100)')
        bar_color = Udata(atuple('bar_color'), 'rgba(255, 255, 255, 100)')
        border_radius = Udata(atuple('border_radius'), 6)
        border = Udata(atuple('border'), '1px solid rgba(255, 255, 255, 100)')
        temp_dict = {
            'QProgressBar':{
                'background-color': bg_color,
                'border-top-left-radius': border_radius[0],
                'border-top-right-radius': border_radius[1],
                'border-bottom-left-radius': border_radius[2],
                'border-bottom-right-radius': border_radius[3],
                'border': border,
            },
            'QProgressBar::chunk':{
                'background-color': bar_color,
                'border-top-left-radius': border_radius[0],
                'border-top-right-radius': border_radius[1],
                'border-bottom-left-radius': border_radius[2],
                'border-bottom-right-radius': border_radius[3],
            }
        }
        if not hasattr(self, 'style_dict'):
            self.style_dict = {}
        self.style_dict = process_style_dict(self.style_dict, temp_dict, escape_sign, style_d)
        self.setStyleSheet(style_make(self.style_dict))

class InputLine(QLineEdit):
    def __init__(self, height_f:int, scrollbar_color:str="#C3C3C3", 
                 scrollbar_color_hover:str="#6B6B6B",
                 scrollbar_color_pressed:str="#1F1F1F",
                 ):
        super().__init__()
        self.height_f = height_f
        self.color1 = scrollbar_color
        self.color2 = scrollbar_color_hover
        self.color3 = scrollbar_color_pressed
        #self._style_set()
    
    def _style_set(self):
        #self.setTextInteractionFlags(Qt.TextEditable)  # 保证可编辑
        self.setCursorPosition(0)  # 可选：将光标放置在文本开头
        self.setAlignment(Qt.AlignLeft)  # 确保文本左对齐
        self.setFixedHeight(self.height_f)  
        # self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)  
        # self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  
        self.setTextMargins(10, 0, 10, 0)
        self.setToolTip(self.text())  # 鼠标悬停时显示完整文本
        QToolTip.setFont(QFont("Arial", 10))  # 设置工具提示字体大小
        #self.setWordWrapMode(QTextOption.NoWrap)
        self.scroll_bar_style_sheet = f'''
        /* 水平滚动条 */
        QScrollBar:horizontal {{
            height: 16px;
            background: rgba(255, 255, 255, 255);
            border: none;
        }}

        QScrollBar::handle:horizontal {{
            background: {self.color1};
            border-radius: 6px;
            min-width: 20px;
        }}

        QScrollBar::handle:horizontal:hover {{
            background: {self.color2};
        }}

        QScrollBar::handle:horizontal:pressed {{
            background: {self.color3};
        }}

        QScrollBar::add-line:horizontal {{
            border: 1px solid transparent;
            background: transparent;
        }}

        QScrollBar::sub-line:horizontal {{
            border: 1px solid transparent;
            background: transparent;
        }}

        QScrollBar::up-arrow:horizontal, QScrollBar::down-arrow:horizontal {{
            background: transparent;
        }}

        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
            background: transparent;
        }}
        '''
        #self.horizontalScrollBar().setStyleSheet(self.scroll_bar_style_sheet)

class SmartStackWidget(QStackedWidget):
    def __init__(self, parent:QWidget,an_time=200):
        super().__init__(parent)
        self.an_time = an_time
        self._load()
        self.in_animation = False
    
    def _load(self):
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(1)  # 初始透明度

    # def wheelEvent(self, event):
    #     current_index = self.currentIndex()
    #     num_pages = self.count()
    #     if event.angleDelta().y() > 0:  # 向上滚动
    #         new_index = (current_index + 1) % num_pages
    #     else:  
    #         new_index = (current_index - 1 + num_pages) % num_pages
    #     self.setCurrentIndex(new_index)

    def remove_page(self, index:int):
        index_n = self.currentIndex()
        if index == index_n:
            self.setCurrentIndex((index_n+1 ) % self.count())
        widget_to_rm = self.widget(index)
        self.removeWidget(widget_to_rm)
        widget_to_rm.deleteLater()
    
    def animate_transition(self, index: int, sign: int):
        if self.in_animation:
            return
        self.in_animation = True
        current_widget = self.widget(self.currentIndex())
        next_widget = self.widget(index)

        # current_widget.setGeometry(self.geometry())
        # next_widget.setGeometry(self.geometry())

        ori_pos = current_widget.geometry()
        animation_group = QParallelAnimationGroup(self)
        self.current_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.current_animation.setDuration(self.an_time//3)
        self.current_animation.setStartValue(1)
        self.current_animation.setKeyValueAt(0.2, 0.5)
        self.current_animation.setKeyValueAt(0.8, 0.4)
        self.current_animation.setEndValue(0)
        # current_animation.setEndValue(QRect(0, 0, current_widget.width(), current_widget.height()))
        self.current_animation.setEasingCurve(QEasingCurve.OutQuad)

        next_animation = QPropertyAnimation(next_widget, b"geometry")
        next_animation.setDuration(2*self.an_time//3)
        if sign > 0:
            next_animation.setStartValue(QRect(0, self.height(), self.width()-5, self.height()-5))
        else:
            next_animation.setStartValue(QRect(0, -self.height(), self.width()-5, self.height()-5))
        next_animation.setEndValue(QRect(0, 0, self.width(), self.height()))
        next_animation.setEasingCurve(QEasingCurve.OutCubic)

        next_animation2 = QPropertyAnimation(self.opacity_effect, b"opacity")
        next_animation2.setDuration(2*self.an_time//3)
        next_animation2.setStartValue(0)
        next_animation2.setEndValue(1)
        animation_group.addAnimation(next_animation)
        animation_group.addAnimation(next_animation2)
        next_animation.setEasingCurve(QEasingCurve.OutCubic)

        # animation_group.addAnimation(current_animation)
        # animation_group.start()
        self.current_animation.start()
        self.current_animation.finished.connect(lambda: self.animation_later(current_widget, next_widget, animation_group, sign))

    def animation_later(self, current_widget, next_widget, later_animation,sign):
        current_widget.hide()
        next_widget.hide()
        self.opacity_effect.setOpacity(1)
        self.setCurrentWidget(next_widget)
        if sign > 0:
            next_widget.setGeometry(QRect(0, self.height(), self.width()-5, self.height()-5))
        else:
            next_widget.setGeometry(QRect(0, -self.height(), self.width()-5, self.height()-5))
        next_widget.show()
        self.l_animation = later_animation

        self.l_animation.start()
        self.l_animation.finished.connect(self.animation_end)

    def animation_end(self):
        self.in_animation = False

    # def wheelEvent(self, event):
    #     if event.angleDelta().y() > 0:
    #         self.setIndex(self.currentIndex()-1)
    #     else:
    #         self.setIndex(self.currentIndex()+1)

    def setIndex(self, index):
        index = min(max(0, index), self.count()-1)
        if index != self.currentIndex():
            if index < self.currentIndex():
                self.animate_transition(index, sign=-1)
            else:
                self.animate_transition(index, sign=1)
            #self.setCurrentIndex(index)

class TipButton(QPushButton):
    def __init__(self, style_d:dict, text_f:str, font_f:QFont=QFont(), width_f=None, height_f=None, radius_set:List[bool]=[True, True, True, True]):
        super().__init__()
        UIUpdater.set(text_f, self.setText, 'text')
        UIUpdater.set(font_f, self.setFont, 'font')
        UIUpdater.set(width_f, self.setFixedWidth, 'width')
        UIUpdater.set(height_f, self.setFixedHeight, 'height')
        self.radius_set = radius_set
        UIUpdater.set(style_d, self.customStyle, 'style')

    def customStyle(self, style_d:dict, escape_sign:dict={}):
        bg_colors = Udata(atuple('background_colors'), ['#F7F7F7', '#FFC300', '#FF5733'])
        font_colors = Udata(atuple('font_colors'), ['#000000', '#000000', '#000000'])
        border = Udata(atuple('border'), 'none')
        border_radius = Udata(atuple('border_radius'), 6)
        padding = Udata(atuple('padding'), [5, 5, 5, 5])
        temp_dict = {}
        self.style_dict = {
            'QPushButton':{
                'background-color': bg_colors[0],
                'color': font_colors[0],
                'border': border,
                'border-top-left-radius': border_radius[0],
                'border-top-right-radius': border_radius[1],
                'border-bottom-left-radius': border_radius[2],
                'border-bottom-right-radius': border_radius[3],
                'padding': padding,
            },
            'QPushButton::hover':{
                'background-color': bg_colors[1],
                'color': font_colors[1],
            },
            'QPushButton::pressed':{
                'background-color': bg_colors[2],
                'color': font_colors[2],
            },
        }
        self.style_sheet = style_make(self.style_dict)
        self.setStyleSheet(self.style_sheet)

class AutoMenu(QWidget):
    action_signal = Signal(dict)
    def __init__(self, style_d:dict, action_value:dict,font:QFont=QFont(), width_f=None, height_f=None):
        super().__init__()
        self.width_f = width_f
        self.height_f = height_f
        self.action_value = action_value
        self.style_d = style_d
        self.font_f = font
        self.setWindowFlags(self.windowFlags()|Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setAttribute(Qt.WA_TranslucentBackground)  # 设置窗口属性为透明
        # self.setWindowOpacity(1)
        self._init_action()
        UIUpdater.set(self.font_f, self.setFont, 'font')
        # self.move_signal.connect(self.async_Move)
        self.relative_position = QPoint(0, 0)
    
    def eventFilter(self, obj, event):
        if self.isVisible():
            if event.type() == QEvent.ActivationChange:
                if not self.isActiveWindow():
                    self.hide()  # 隐藏菜单
                    QApplication.instance().removeEventFilter(self)
            elif event.type() == QEvent.MouseButtonPress:
                if not self.geometry().contains(event.globalPos()):
                    self.hide()
                    QApplication.instance().removeEventFilter(self)
        return super().eventFilter(obj, event)
    
    def _init_action(self)->None:
        self.layout_0 = amlayoutV(align_h='l')
        self.setLayout(self.layout_0)
        spacing_f = UIUpdater.config[atuple('Settings','LauncherSetting','style','tab_menu','item','spacing')]
        
        spacing_n = spacing_f if spacing_f else 0
        self.layout_0.setSpacing(spacing_n)
        for i, action_i in enumerate(self.action_value.keys()):
            if i == 0:
                button_i = YohoPushButton(style_config=self.style_d|atuple('item'), text_f=action_i, font_f=self.font_f, width_f=self.width_f, height_f=self.height_f)
                button_i.extra_style_dict = {'QPushButton':
                                             { 'border-bottom-left-radius':0, 
                                              'border-bottom-right-radius':0}}
                button_i.setStyleSheet(style_make(button_i.style_dict|button_i.extra_style_dict))
            elif i == len(self.action_value.keys())-1:
                button_i = YohoPushButton(style_config=self.style_d|atuple('item'), text_f=action_i, font_f=self.font_f, width_f=self.width_f, height_f=self.height_f)
                button_i.extra_style_dict = {'QPushButton':
                                             { 'border-top-left-radius':0, 
                                              'border-top-right-radius':0}}
                button_i.setStyleSheet(style_make(button_i.style_dict|button_i.extra_style_dict))
            else:
                button_i = YohoPushButton(style_config=self.style_d|atuple('item'), text_f=action_i, font_f=self.font_f, width_f=self.width_f, height_f=self.height_f)
                button_i.extra_style_dict = {'QPushButton':
                                             { 'border-top-left-radius':0, 
                                              'border-top-right-radius':0,
                                              'border-bottom-left-radius':0,
                                              'border-bottom-right-radius':0}}
                button_i.setStyleSheet(style_make(button_i.style_dict|button_i.extra_style_dict))
            self.layout_0.addWidget(button_i)
    
    def _action(self, action_name:str, action_value:str)->None:
        self.action_signal.emit({'geometry':self.geometry(), 'tab_index':self.tab_index, 'action_name':action_name, 'action_value':action_value})
        self.hide()
    
    def action(self, index:int, relative_position:QPoint, parent_pos:QPoint)->None:
        self.tab_index = index
        self.relative_position = relative_position
        x = self.relative_position.x() + parent_pos.x()
        y = self.relative_position.y() + parent_pos.y()
        self.setGeometry(x, y, self.width(), self.height())
        self.adjustSize()
        self.show()
        self.raise_()
        QApplication.instance().installEventFilter(self)
        # QApplication.instance().installEventFilter(self)