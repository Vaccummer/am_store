from PySide2.QtWidgets import QApplication, QPushButton, QWidget, QVBoxLayout
from PySide2.QtCore import Qt

class WheelButton(QPushButton):
    def __init__(self, text, parent=None):
        super(WheelButton, self).__init__(text, parent)

    def wheelEvent(self, event):
        # 检查滚轮方向
        if event.angleDelta().y() > 0:
            self.setText("滚轮向上")
        else:
            self.setText("滚轮向下")
        # 你可以在这里添加其他响应鼠标滚轮的操作
        event.accept()

app = QApplication([])

# 创建主窗口
window = QWidget()
window.setWindowTitle("滚轮响应按钮")

# 创建一个布局
layout = QVBoxLayout()

# 创建一个自定义的 WheelButton
wheel_button = WheelButton("滚动鼠标滚轮")

# 将自定义按钮添加到布局
layout.addWidget(wheel_button)

# 设置窗口布局
window.setLayout(layout)
window.show()
app.exec_()
