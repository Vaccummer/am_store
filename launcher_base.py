from PySide2.QtWidgets import QApplication, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QApplication, QMainWindow, QComboBox, QVBoxLayout, QLabel
from PySide2.QtWidgets import QWidget, QTextEdit, QProgressBar, QToolButton, QPushButton, QFrame, QSystemTrayIcon, QMenu
from PySide2.QtWidgets import QVBoxLayout, QHBoxLayout, QFileDialog, QGraphicsBlurEffect, QScrollArea, QAction, QShortcut
from PySide2.QtCore import Qt, QEvent, QObject, Signal, QSize, Slot, QThread
from PySide2.QtCore import QTimer, QPropertyAnimation, QEasingCurve, QSequentialAnimationGroup
from PySide2.QtGui import QPixmap, QPalette, QIcon, QFont, QScreen, QFontMetrics, QWindow, QKeySequence
from PySide2.QtGui import QPainter, QColor, QBrush, QPen, QLinearGradient, QTextCharFormat, QTextCursor
from Scripts.tools.toolbox import *

class Launcher_Base(QMainWindow):
    def __init__(self, config:dict, app:QApplication):
        super().__init__()
        self.wkdir = os.getcwd()
        self.config = Config_Manager(wkdir=self.wkdir, 
                                     config=config, 
                                     mode_name=None,
                                     widget_name=None,
                                     obj_name=None,)
        self.app = app
        self._para_needed()
    # For mouse control
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.isNearEdge(event.pos()):
                self.edge_drag = event.pos()
                self.original_geometry = self.geometry()
                event.accept()
            else:
                x, y, w, h = self.get_geometry(self.switch_button)
                if event.y() >y+h or event.x() > x+w:
                    self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
                    event.accept()
        else:
            super().mousePressEvent(event)
    def mouseMoveEvent(self, event):
        if self.edge_drag:
            self.resizeWindow(event.pos())
        elif self.drag_position and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
        else:
            super().mouseMoveEvent(event)
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = None
            self.edge_drag = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    def _para_needed(self):
        # for mouse click enven judge
        self.drag_position = None
        self.edge_drag = None
        self.edge_threshold = int(self.gap/3.5)
    @staticmethod
    def programm_exit():
        ## programm exit
        QApplication.instance().quit()
    @staticmethod
    def get_geometry(window_f):
        geom_f = window_f.geometry()
        return[geom_f.x(), geom_f.y(), geom_f.width(), geom_f.height()]
    
