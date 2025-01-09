from PySide2.QtWidgets import QTextEdit
from PySide2.QtGui import QTextCursor

class CustomTextEdit(QTextEdit):
    def __init__(self):
        super().__init__()
        # 设置为单行模式
        self.setLineWrapMode(QTextEdit.NoWrap)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 获取并设置文本光标
        cursor = self.textCursor()
        # 设置光标属性
        ...