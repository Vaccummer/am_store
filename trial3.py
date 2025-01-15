import os
from win32com.client import Dispatch

def is_shortcut(path):
    """
    判断一个文件是否是快捷方式。
    :param path: 文件路径
    :return: 如果是快捷方式，返回 True；否则返回 False
    """
    return os.path.isfile(path) and path.lower().endswith('.lnk')

def resolve_shortcut(path):
    """
    获取快捷方式指向的真实路径。
    :param path: 快捷方式路径
    :return: 指向的真实路径
    """
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortcut(path)
    return shortcut.TargetPath

# 示例使用
shortcut_path = r"F:\Windows_Data\Desktop_File\HWiNFO64.exe - Shortcut.lnk"

if is_shortcut(shortcut_path):
    real_path = resolve_shortcut(shortcut_path)
    print(f"快捷方式指向的真实路径是: {real_path}")
else:
    print(f"{shortcut_path} 不是快捷方式")
