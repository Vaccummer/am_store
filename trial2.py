from PySide2.QtCore import Qt
from PySide2.QtGui import QDragEnterEvent, QDropEvent
from PySide2.QtWidgets import QApplication, QTextEdit


class DragDropTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)  # 启用拖放功能

    def focusNextPrevChild(self, next):
        # 阻止焦点切换
        return True

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():  # 检查是否有文件 URL
            event.acceptProposedAction()  # 接受拖入
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event: QDropEvent):
        print(2)
        mime_data = event.mimeData()
        if mime_data.hasUrls():  # 如果拖放的内容是文件
            urls = mime_data.urls()
            paths = [url.toLocalFile() for url in urls]  # 获取文件路径
            self.append("Dropped files:\n" + "\n".join(paths))  # 显示文件路径
            event.acceptProposedAction()  # 接受拖放
        else:
            super().dropEvent(event)


if __name__ == "__main__":
    app = QApplication([])
    editor = DragDropTextEdit()
    editor.setText("Drag and drop files here.")
    editor.show()
    app.exec_()
