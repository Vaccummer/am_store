from PySide2.QtGui import QFont, QFontDatabase
from PySide2.QtWidgets import QApplication, QLabel
from PySide2.QtCore import Qt
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
app = QApplication([])

# 创建全局字体
font = QFont("Arial", 10, 40)
font.setStyleStrategy(QFont.PreferAntialias)  # 设置抗锯齿策略
app.setFont(font)

label = QLabel("Hello, Anti-Aliased Text!")
label.setAlignment(Qt.AlignCenter)
label.show()

app.exec_()
