import os
import ctypes
from win32con import *
from win32api import *
from win32gui import *
from win32com.shell import shell, shellcon

def get_default_icon(extension):
    """
    获取指定扩展名的默认图标
    :param extension: 文件扩展名，例如 '.txt', '.pdf', '.jpg' 等
    :return: 图标句柄
    """
    # 获取文件扩展名的图标路径及索引
    icon_info = shell.SHGetFileInfo(
        extension, 0, shellcon.SHGFI_ICON | shellcon.SHGFI_SYSICONINDEX
    )

    # icon_info 是一个元组 (图标路径, 图标索引)
    icon_handle = icon_info[0]

    # 获取图标句柄
    icon = ExtractIcon(0, icon_handle, icon_info[1])

    return icon

# 测试：获取 .txt 文件类型的默认图标
icon = get_default_icon(".txt")
print(icon)
