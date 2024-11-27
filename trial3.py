import sys
from PySide2.QtWidgets import QApplication, QTabWidget, QTabBar, QScrollArea, QVBoxLayout, QHBoxLayout, QWidget
from PySide2.QtCore import Qt


class CustomTabBar(QTabBar):
    def wheelEvent(self, event):
        # 滚动TabBar的视野而不是切换标签
        delta = event.angleDelta().y()
        scroll_bar = self.parentWidget().horizontalScrollBar()
        scroll_bar.setValue(scroll_bar.value() - delta // 2)


class ScrollableTabWidget(QTabWidget):
    def __init__(self):
        super().__init__()

        # 替换默认的 QTabBar 为自定义的 CustomTabBar
        self.tab_bar = CustomTabBar()
        self.setTabBar(self.tab_bar)

        # 创建一个 QScrollArea 用于包装自定义 TabBar
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # 将自定义 TabBar 嵌入到 QScrollArea
        self.tab_bar.setParent(self.scroll_area)
        self.scroll_area.setWidget(self.tab_bar)

        # 重新设置布局以包含 QScrollArea 和 QTabWidget 的内容
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)

        # 添加滚动区域作为顶部标签栏
        self.tab_container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(self.scroll_area)
        self.tab_container.setLayout(container_layout)

        self.layout.addWidget(self.tab_container)

        # 设置主窗口布局
        self.main_container = QWidget()
        self.main_container.setLayout(self.layout)
        self.layout_widget = QWidget()
        self.layout.addWidget(self)

        self.setParent(self.main_container)

        # 添加 Tabs 示例
        for i in range(20):
            self.addTab(QWidget(), f"Tab {i+1}")

    def addTab(self, widget, label):
        # 添加 Tab 同时更新 CustomTabBar
        super().addTab(widget, label)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 创建窗口并显示
    window = QWidget()
    layout = QVBoxLayout(window)

    tab_widget = ScrollableTabWidget()
    layout.addWidget(tab_widget)

    window.setLayout(layout)
    window.resize(800, 600)
    window.setWindowTitle("Scrollable Tab Widget")
    window.show()

    sys.exit(app.exec_())
