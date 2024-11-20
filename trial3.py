from PySide2.QtCore import Qt, QTimer
from PySide2.QtWidgets import QApplication, QWidget, QProgressBar, QVBoxLayout
class ProgressBarExample(QWidget):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("进度条示例")
        self.setGeometry(100, 100, 300, 100)  # 设置窗口位置和大小
        
        # 创建进度条
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)  # 设置进度条的最小值和最大值
        self.progress_bar.setValue(0)  # 初始进度值为0
        self.progress_bar.setTextVisible(False)  # 显示进度百分比文本
        
        # 创建布局，并将进度条添加到布局中
        layout = QVBoxLayout(self)
        layout.addWidget(self.progress_bar)
        
        # 定时器，每50毫秒更新一次进度条
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(50)
        
        self.progress = 0  

    def update_progress(self):
        """更新进度条的值"""
        if self.progress < 100:
            self.progress += 1
            self.progress_bar.setValue(self.progress)
        else:
            self.timer.stop()  # 停止计时器，表示任务完成
            self.progress_bar.setValue(0)

if __name__ == "__main__":
    app = QApplication([])
    
    window = ProgressBarExample()
    window.show()
    
    app.exec_()
