from PySide2.QtGui import QScreen
from PySide2.QtWidgets import QApplication

def get_screen_info():
    app = QApplication([])  # QApplication 对象
    screen = app.primaryScreen()  # 获取主屏幕对象

    # 获取像素尺寸
    pixel_size = screen.size()
    width_px = pixel_size.width()
    height_px = pixel_size.height()

    # 获取物理尺寸（毫米）
    physical_size = screen.physicalSize()
    width_mm = physical_size.width()
    height_mm = physical_size.height()

    # 获取屏幕DPI（dots per inch, 像素密度）
    dpi = screen.physicalDotsPerInch()

    print(f"屏幕像素尺寸: {width_px} x {height_px} px")
    print(f"屏幕物理尺寸: {width_mm} x {height_mm} mm")
    print(f"屏幕 DPI: {dpi} dpi")

    app.quit()
get_screen_info()