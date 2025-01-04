from PySide2.QtWidgets import (
    QApplication,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QGraphicsOpacityEffect,
)
from PySide2.QtCore import QPropertyAnimation, QEasingCurve

class OpacityWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # 创建按钮
        self.fade_in_button = QPushButton("Fade In", self)
        self.fade_out_button = QPushButton("Fade Out", self)

        # 布局
        layout = QVBoxLayout(self)
        layout.addWidget(self.fade_in_button)
        layout.addWidget(self.fade_out_button)
        self.setLayout(layout)

        # 设置透明效果
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(1.0)  # 初始透明度

        # 绑定事件
        self.fade_in_button.clicked.connect(self.fade_in)
        self.fade_out_button.clicked.connect(self.fade_out)

    def fade_in(self):
        """部件渐显"""
        animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        animation.setDuration(1000)  # 动画持续时间（毫秒）
        animation.setStartValue(0.5)  # 起始透明度
        animation.setEndValue(1.0)  # 结束透明度
        animation.setEasingCurve(QEasingCurve.InOutQuad)  # 缓动效果
        animation.start()

    def fade_out(self):
        """部件渐隐"""
        animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        animation.setDuration(1000)  # 动画持续时间（毫秒）
        animation.setStartValue(1.0)  # 起始透明度
        animation.setEndValue(0.5)  # 结束透明度
        animation.setEasingCurve(QEasingCurve.InOutQuad)  # 缓动效果
        animation.start()

if __name__ == "__main__":
    app = QApplication([])
    widget = OpacityWidget()
    widget.setWindowTitle("Widget Opacity Example")
    widget.resize(300, 200)
    widget.show()
    app.exec_()
