import os
import sys
from PySide2.QtWidgets import QApplication, QListWidget, QListWidgetItem
from PySide2.QtCore import QMimeData, Qt
from PySide2.QtGui import QDrag


class DraggableListWidget(QListWidget):
    def __init__(self):
        super().__init__()
        self.setSelectionMode(QListWidget.SingleSelection)
        self.setDragEnabled(True)

    def startDrag(self, supportedActions):
        # 获取当前选中的项
        item = self.currentItem()
        if item:
            mime_data = QMimeData()

            # 创建一个实际存在的临时文件
            file_name = item.text() + ".txt"
            temp_dir = os.environ["TEMP"]
            temp_file_path = os.path.join(temp_dir, file_name)

            # 写入临时文件内容
            with open(temp_file_path, "w") as f:
                f.write("This is a test file.")

            # 设置 MIME 数据类型为支持拖拽到文件管理器的格式
            url = f"file:///{temp_file_path.replace(os.sep, '/')}"
            mime_data.setUrls([url])

            # 创建拖拽操作
            drag = QDrag(self)
            drag.setMimeData(mime_data)

            # 可选：设置拖拽的视觉效果
            drag.exec_(Qt.CopyAction)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DraggableListWidget()

    # 添加示例项
    for i in range(5):
        item = QListWidgetItem(f"Item {i + 1}")
        window.addItem(item)

    window.setWindowTitle("Draggable QListWidget")
    window.resize(400, 300)
    window.show()
    sys.exit(app.exec_())
