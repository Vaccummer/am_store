from PySide2.QtWidgets import QApplication, QLineEdit, QVBoxLayout, QWidget
from PySide2.QtCore import Qt


class LineEditWithProgress(QWidget):
    def __init__(self):
        super().__init__()

        # 创建 QLineEdit
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText("输入文本以更新进度...")
        self.line_edit.setAlignment(Qt.AlignLeft)

        # 初始化布局
        layout = QVBoxLayout(self)
        layout.addWidget(self.line_edit)

        # 设置样式表
        self.line_edit.setStyleSheet("""
            QLineEdit {
                border: 2px solid gray;
                border-radius: 5px;
                padding: 2px;
            }
            QLineEdit::before {
                content: "";
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 green, stop:1 transparent);
                height: 100%;
                border-radius: 5px;
                z-index: -1;
            }
        """)

        # 绑定文本事件
        self.line_edit.textChanged.connect(self.update_style)

    def update_style(self):
        # 动态更新背景颜色进度条
        max_length = 100
        current_length = len(self.line_edit.text())
        progress = min(100, (current_length / max_length) * 100) / 100

        # 更新样式表，动态设置背景
        self.line_edit.setStyleSheet(f"""
            QLineEdit {{
                border: 2px solid gray;
                border-radius: 5px;
                padding: 2px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 green, stop:{progress} green, stop:{progress} transparent);
            }}
        """)


if __name__ == "__main__":
    app = QApplication([])
    window = LineEditWithProgress()
    window.show()
    app.exec_()
