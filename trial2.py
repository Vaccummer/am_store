import sys
from PySide2.QtWidgets import QApplication, QTabWidget, QTabBar, QVBoxLayout, QWidget, QScrollArea
from PySide2.QtCore import Qt


class CustomTabBar(QTabBar):
    def __init__(self, parent):
        self.up = parent
        super().__init__()
        self.setMouseTracking(True)

    def wheelEvent(self, event):
        # redefine the wheel event to scroll the tab bar
        #super().wheelEvent(event)
        self.up.scroll_right(50)
        #event.ignore()

class TabBarOnlyWidget(QWidget):
    def __init__(self):
        super().__init__()

        # 创建一个 QScrollArea 用于包装 TabBar
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # 自定义 TabBar
        self.tab_bar = CustomTabBar(self)
        self.scroll_area.setWidget(self.tab_bar)

        # 创建布局，用于放置滚动区域
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.scroll_area)

        self.setLayout(layout)
        self.tab_bar.setStyleSheet("""
        QTabBar{
            border: none;
            padding: 8px;
            background: transparent; /* 可选：设置背景透明 */
        }
        QTabBar::tab {
            background: lightgray;
            border: none;
            border-radius: 8px;
            padding: 8px;
        }
        QTabBar::tab:selected {
            background: white;
            font-weight: bold;
        }
        QTabBar::tab:hover {
            background: #f0f0f0;                
        }
        QTabBar::tab:!selected {
            margin-top: 2px; /* 未选中标签距离顶部的间距 */
        }
    """)
        # 添加示例 Tabs
        for i in range(5):
            self.addTab(f"Tab {i + 1}")

    def addTab(self, label):
        # 动态添加标签
        self.tab_bar.addTab(label)
    
    def scroll_right(self, index:int):
        # 模拟向右滑动
        scroll_bar = self.scroll_area.horizontalScrollBar()
        current_value = scroll_bar.value()  
        new_value = max(scroll_bar.minimum(), min(current_value + index, scroll_bar.maximum()))  
        scroll_bar.setValue(new_value)  

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 创建 TabBar 只显示标签部分
    window = TabBarOnlyWidget()
    window.resize(800, 100)
    window.setWindowTitle("Tab Bar Only Widget")
    window.show()

    sys.exit(app.exec_())
