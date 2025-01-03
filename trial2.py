from PySide2.QtWidgets import QApplication, QMainWindow, QComboBox, QVBoxLayout, QWidget
from PySide2.QtGui import QPalette, QColor
from PySide2.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        combo = QComboBox()
        combo.addItems(["Option 1", "Option 2", "Option 3"])
        
        # First set stylesheet for border, radius etc
        combo.setStyleSheet("""
            QComboBox {
                background-color: #4CC1B5;
                border: 2px solid #4CC1B5;
                border-radius: 5px;
                padding: 5px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                width: 20px;
                height: 20px;
            }
        """)
        
        # Then use QPalette for background color
        palette = combo.palette()
        palette.setColor(QPalette.Button, QColor('red'))
        palette.setColor(QPalette.Base, QColor('black'))
        combo.setPalette(palette)
        layout.addWidget(combo)

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()