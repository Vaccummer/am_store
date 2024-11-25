import sys
from PySide2.QtWidgets import QApplication, QWidget, QTextEdit, QVBoxLayout
from PySide2.QtCore import Qt
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

class MyWindow(QWidget):
    def __init__(self):
        super().__init__()

        # 创建 QTextEdit
        text_edit = QTextEdit(self)

        # 设置文本框为单行模式，禁用自动换行
        text_edit.setPlainText("This is a single line text that will not wrap.")  # 设置默认文本
        text_edit.setWordWrapMode(QTextOption.NoWrap)  # 禁用换行

        # 禁用垂直滚动条
        text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 设置自定义滚动条样式
        self.set_scrollbar_style(text_edit)

        # 创建布局并添加控件
        layout = QVBoxLayout()
        layout.addWidget(text_edit)
        self.setLayout(layout)

        # 设置窗口属性
        self.setWindowTitle("QTextEdit with Disabled Vertical Scrollbar")
        self.resize(400, 50)  # 设置窗口的大小

    def set_scrollbar_style(self, widget):
        """设置 QTextEdit 滚动条的样式"""
        style = """
        /* 水平滚动条 */
        QScrollBar:horizontal {
            height: 16px;
            background: rgba(255, 255, 255, 255);
            border: none ;
        }

        QScrollBar::handle:horizontal {
            background: #C3C3C3;
            border-radius: 6px;
            min-width: 20px;
        }

        QScrollBar::handle:horizontal:hover {
            background: #6B6B6B;
        }

        QScrollBar::handle:horizontal:pressed {
            background: #1F1F1F;
        }

        QScrollBar::add-line:horizontal {
            border: 1px solid transparent;
            background: transparent;
        }

        QScrollBar::sub-line:horizontal {
            border: 1px solid transparent;
            background: transparent;
        }

        QScrollBar::up-arrow:horizontal, QScrollBar::down-arrow:horizontal {
            background: transparent;
        }

        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
            background: transparent;
        }
        """
        # 设置样式表
        widget.setStyleSheet(style)

# 创建应用程序和窗口实例
app = QApplication(sys.argv)
window = MyWindow()
window.show()

sys.exit(app.exec_())
