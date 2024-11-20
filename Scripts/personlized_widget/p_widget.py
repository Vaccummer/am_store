from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from typing import Literal, Optional, Tuple, Union, List
from abc import abstractmethod


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
        self.setFixedSize(int(1.3*self.iconSize().width()), int(1.3*self.iconSize().width()))
        self.an_time = an_time
        self.change_size = change_size
        self.change_period = change_period
        # 设置按钮背景透明
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




