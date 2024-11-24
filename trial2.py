from PySide2.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PySide2.QtCore import Qt

class MyWindow(QWidget):
    def __init__(self):
        super().__init__()

        # 创建顶层垂直布局
        outer_layout = QVBoxLayout()

        # 创建内部布局（另一个垂直布局）
        inner_layout = QVBoxLayout()

        # 添加按钮到内部布局
        button1 = QPushButton("Button 1")
        button2 = QPushButton("Button 2")
        button3 = QPushButton("Button 3")

        # 添加按钮到内部布局
        inner_layout.addWidget(button1)
        inner_layout.addWidget(button2)
        inner_layout.addWidget(button3)

        # 设置内部布局的对齐方式为右对齐
        inner_layout.setAlignment(Qt.AlignRight)

        # 创建外部按钮，并添加到外部布局
        outer_button = QPushButton("Outer Button")

        # 将内部布局和外部按钮添加到顶层布局
        outer_layout.addWidget(outer_button)
        outer_layout.addLayout(inner_layout)

        # 设置顶层布局的对齐方式为右对齐
        outer_layout.setAlignment(Qt.AlignRight)

        # 设置窗口的布局
        self.setLayout(outer_layout)

        # 设置窗口标题
        self.setWindowTitle("Right Aligning Widgets in Nested Layouts")

# 创建应用并显示窗口
app = QApplication([])
window = MyWindow()
window.show()
app.exec_()
