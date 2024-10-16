from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from typing import Literal, Optional, Tuple, Union



class YohoPushButton(QPushButton):
    def __init__(self, icon_i:Union[str, QIcon], 
                 size:Union[int, QSize], 
                 an_type:Literal["shake", 'resize', None]=None, 
                 an_time:int=180,
                 change_size:float=0.6,
                 change_period:float=0.7):
        super().__init__()

        # 设置按钮图标
        icon_i = icon_i if isinstance(icon_i, QIcon) else QIcon(icon_i)
        self.setIcon(icon_i)
        self.size_f = size if isinstance(size, QSize) else QSize(size, size)
        self.setIconSize(self.size_f)
        self.setFixedSize(int(1.2*self.iconSize().width()), int(1.2*self.iconSize().width()))
        self.an_time = an_time
        self.change_size = change_size
        self.change_period = change_period
        # 设置按钮背景透明
        self.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
            }
        """)

        if an_type == "shake":
            self.clicked.connect(self.shake_icon)
        elif an_type == "resize":
            self.clicked.connect(self.resize_icon)

    def shake_icon(self):
        self.animation = QPropertyAnimation(self, b"geometry")
        start_rect = self.geometry()
        self.animation.setDuration(self.an_time)
        self.animation.setKeyValueAt(0, QRect(start_rect))
        self.animation.setKeyValueAt(0.2, QRect(start_rect.x() - 5, start_rect.y(), start_rect.width(), start_rect.height()))
        self.animation.setKeyValueAt(0.4, QRect(start_rect.x() + 5, start_rect.y(), start_rect.width(), start_rect.height()))
        self.animation.setKeyValueAt(0.6, QRect(start_rect.x() - 5, start_rect.y(), start_rect.width(), start_rect.height()))
        self.animation.setKeyValueAt(0.8, QRect(start_rect.x() + 5, start_rect.y(), start_rect.width(), start_rect.height()))
        self.animation.setKeyValueAt(1, QRect(start_rect))
        self.animation.start()
    
    def resize_icon(self):
        # 创建放大缩小动画
        self.animation = QPropertyAnimation(self, b"iconSize")
        
        # 动画持续时间为 500 毫秒
        self.animation.setDuration(self.an_time)
        size_n = QSize(int(self.change_size*self.size_f.width()), int(self.change_size*self.size_f.height()))
        # 设置动画的起始大小（默认大小）和目标大小（放大的大小）
        self.animation.setStartValue(self.size_f)
        self.animation.setKeyValueAt(self.change_period, size_n)  # 放大到100x100
        self.animation.setEndValue(self.size_f)  # 返回到默认大小

        # 开始动画
        self.animation.start()

class ColorfulButton(QPushButton):
    def __init__(self, text:str, font:QFont, ori_color:str, hover_color:str, click_color:str):
        super().__init__()
        self.setText(text)
        self.setFont(font)
        self.ori_color = ori_color
        self.hover_color = hover_color
        self.click_color = click_color
    def _initUI(self):
        self.setStyleSheet(f'''
                            QPushButton {{
                            padding: 10px;
                            color: #fff;
                            border: none;
                            border-radius: 10px;
                            background-color: {self.ori_color};
                        }}
                        QPushButton:hover {{
                            background-color: {self.hover_color}; 
                        }}
                        QPushButton:pressed {{
                                background-color: {self.click_color};
                        }}
                        ''')

class AutoLabel(QLabel):
    def __init__(self, text:str, font:QFont, color:str="#171818"):
        super().__init__()
        self.setText(text)
        self.setFont(font)
        self.set_color(color)
        self.setAlignment(Qt.AlignCenter)
    def set_text(self, text:str):
        self.setText(text)
        self.adjustSize()
    def set_color(self, color:str):
        pass
        # self.setStyleSheet(f'''
        #                    QLabel {{
        #                     color: {color};  # 字体颜色
        #                     background-color: transparent;  # 背景透明
        #                     }}
        #                     ''')


