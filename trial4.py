import sys
from PySide2.QtCore import Qt
from PySide2.QtGui import QFont
from PySide2.QtWidgets import QApplication, QLabel

# 启用高 DPI 支持
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

app = QApplication([])

# 设置字体
font = QFont("jetbrains mono", 12, 70)
font.setStyleStrategy(QFont.PreferAntialias)
font.setStyleHint(QFont.Monospace)
font.setHintingPreference(QFont.PreferFullHinting)
app.setFont(font)

# 创建标签并设置样式
label = QLabel("Hello, Cascadia Code!\nOptimized for PySide2")
label.setAlignment(Qt.AlignCenter)
label.setStyleSheet("background-color: #FFFFFF; color: #000000;")
label.resize(600, 400)
label.show()

sys.exit(app.exec_())
