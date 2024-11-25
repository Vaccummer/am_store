from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
import random
from typing import Literal, Optional, Tuple, Union, List
from abc import abstractmethod

class Asize(QSize):
    def __init__(self, width:int, height:int):
        super().__init__(width, height)
    def __mul__(self, c:Union[int, float]):
        return QSize(int(self.width()*c), int(self.height()*c))
    def q(self):
        return QSize(self.width(), self.height())

class YohoPushButton(QPushButton):
    def __init__(self, icon_i:Union[str, QIcon], 
                 size_f:Union[int, Asize], 
                 an_type:Literal["shake", 'resize', None]=None, 
                 an_time:int=180,
                 change_size:float=0.6,
                 change_period:float=0.7):
        super().__init__()

        # 设置按钮图标
        icon_i = icon_i if isinstance(icon_i, QIcon) else QIcon(icon_i)
        self.setIcon(icon_i)
        if isinstance(size_f, int):
            size_f = QSize(size_f, size_f)
        elif isinstance(size_f, QSize):
            pass
        elif isinstance(size_f, list):
            size_f = QSize(*size_f)
        # if isinstance(size_f, Asize):
        #     #size_t = 1.1*size_f
        #     self.size_f = size_f.q()
        # else:
        self.size_f = QSize(int(size_f.width()*0.9), int(size_f.width()*0.9))
            #size_t = QSize(size_f.width(), size_f.height())
        self.setIconSize(self.size_f)
        self.setFixedSize(size_f)
        self.an_time = an_time
        self.change_size = change_size
        self.change_period = change_period
        self.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                text-align: center; 
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
        size_n = QSize(int(self.change_size*self.size_f.width()), int(self.change_size*self.size_f.height()))
        self.animation.setStartValue(self.size_f)
        self.animation.setKeyValueAt(self.change_period, size_n)  
        self.animation.setEndValue(self.size_f.q() if isinstance(self.size_f, Asize) else self.size_f)  
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

class ProgressBar(QProgressBar):
    def __init__(self, parent:QMainWindow, max_value:float, 
                 height:int, 
                 background_color:str='#E0E0E0', 
                 color_gradient:List[str]=['#DF461CC1', '#069D40FF'],
                 position_gradient:List[float]=[0, 1],
                 show_text:bool=False):
        super().__init__(parent)
        self.height_f = height
        self.max_value = max_value
        self.background_color = background_color
        self.color_gradient = color_gradient
        self.position_gradient = position_gradient
        self.setRange(0, max_value)  
        self.setValue(0)  
        self.progress=0
        self.custom_ui()
        self.setTextVisible(show_text)  
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(50)
    @abstractmethod
    def update_progress(self):
        pass
    def custom_ui(self):
        match len(self.color_gradient):
            case 2:
                self.color_g = f"qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: {self.position_gradient[0]} {self.color_gradient[0]}, stop: {self.position_gradient[1]} {self.color_gradient[1]})"
            case 3:
                self.color_g = f"qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: {self.position_gradient[0]} {self.color_gradient[0]}, stop: {self.position_gradient[1]} {self.color_gradient[1]}, stop: {self.position_gradient[2]} {self.color_gradient[2]})"
            case 4:
                self.color_g = f"qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: {self.position_gradient[0]} {self.color_gradient[0]}, stop: {self.position_gradient[1]} {self.color_gradient[1]}, stop: {self.position_gradient[2]} {self.color_gradient[2]}, stop: {self.position_gradient[3]} {self.color_gradient[3]})"
            case _:
                self.color_g = "qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #DF461CC1, stop: 1 #069D40FF)"
        self.setFixedHeight(self.height_f)
        self.border_radius = self.height_f // 2
        self.stylesheet = f'''
        QProgressBar {{
            border-radius: {self.border_radius}px;
            background-color: {self.background_color};
            border: 0px solid ;
        }}
        QProgressBar::chunk {{
            border-radius: {self.border_radius}px;
            background: {self.color_g};
        }}
        '''
        self.setStyleSheet(self.stylesheet)

class InputLine(QTextEdit):
    def __init__(self, height_f:int, scrollbar_color:str="#C3C3C3", 
                 scrollbar_color_hover:str="#6B6B6B",
                 scrollbar_color_pressed:str="#1F1F1F",
                 ):
        super().__init__()
        self.height_f = height_f
        self.color1 = scrollbar_color
        self.color2 = scrollbar_color_hover
        self.color3 = scrollbar_color_pressed
    def _style_set(self):
        self.setFixedHeight(self.height_f)  
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)  
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  
        self.setTextMargins(10, 0, 10, 0)
        self.setWordWrapMode(QTextOption.NoWrap)
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
        self.horizontalScrollBar().setStyleSheet(self.scroll_bar_style_sheet)
