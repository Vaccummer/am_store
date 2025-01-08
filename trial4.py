import os
from glob import glob
from am_store.common_tools import *
import win32com.client
def get_real_path(lnk_file):
    # 创建一个 Shell 对象
    shell = win32com.client.Dispatch("WScript.Shell")
    # 解析 .lnk 文件
    shortcut = shell.CreateShortCut(lnk_file)
    # 返回目标路径
    return shortcut.Targetpath

src = r'C:\ProgramData\Microsoft\Windows\Start Menu'
path_l = glob(os.path.join(src, '**'), recursive=True)
path_l = [path for path in path_l if not os.path.isdir(path)]
path_lt = []
for path in path_l:
    if path.endswith('.exe'):
        path_lt.append(path)
        continue
    try:
        out = get_real_path(path)
        if out.endswith('.exe'):
            path_lt.append(out)
    except Exception as e:
        pass
path_lt = list(set(path_lt))
for path in path_lt:
    if path.startswith(r'C:\Windows'):
        continue
    elif 'unins' in os.path.basename(path).lower():
        continue
    else:
        print(path)

