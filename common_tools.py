import os
import pickle
import re
import pandas as pd
from win32.lib import win32con
from win32 import win32gui, win32print
# from PySide2.QtGui import QFont
import sys
import shlex
from matplotlib import pyplot as plt
import numpy as np


# turn a string into a formal path of OS
def path_format(string_f):
    if not isinstance(string_f, str):
        raise ValueError(f"Input of path_format function should be a string, but get {type(string_f)}")
    else:
        sep = os.sep
        string_f = rf"{string_f}"
        path_t1 = string_f.replace('/', sep)
        path_t2 = path_t1.replace('\\', sep)
        return path_t2


# function to join str to path
def path_join(*args, mkdir=True):
    path = os.path.join(*args)
    check_flag_f = 0
    if os.path.isdir(path):
        check_flag_f = 0
    else:
        check_flag_f = 1
    if mkdir:
        if check_flag_f == 0:
            os.makedirs(path, exist_ok=True)
        else:
            path_up = os.path.dirname(path)
            os.makedirs(path_up, exist_ok=True)
    return path


# pkl create and read function
def pkl(path_f, data_f=None):
    if not data_f:
        if os.path.exists(path_f):
            with open(path_f, 'rb') as data_f:
                return pickle.load(data_f)
        else:
            print(f'pkl function(read mode) get a illegal path: {path_f}')
            return
    elif path_f and data_f:
        if not os.path.isabs(path_f):
            print(f'pkl function detected no valid path')
            return
        path_f = path_f +'.pkl' if not path_f.endswith('.pkl') else path_f
        with open(path_f, 'wb') as file_f:
            pickle.dump(data_f, file_f)
        return
    else:
        print(f"pkl function get invalid arguments!")
        return
    

# judge a variable whether is a url or not
def is_url(str_f):
    if not isinstance(str_f, str):
        return False
    url_pattern = re.compile(
    r'^(http|https)://'  # 匹配协议部分 http:// 或 https://
    r'([a-zA-Z0-9.-]+)'  # 匹配域名部分
    r'(\.[a-zA-Z]{2,})'   # 匹配顶级域名部分
    )
    match_f = url_pattern.match(str_f)
    return bool(match_f)


# To judge whether a variable is Path or not
def is_path(string_f, exsist_check=False):
    if not isinstance(string_f, str):
        return False
    if not exsist_check:
        return os.path.isabs(string_f)
    else:
        return os.path.exists(string_f)

# Read XLSX doc and transform it into dataframe
def excel_to_df(excel_path_f, region, sheet_f='Sheet1'):
    return pd.read_excel(excel_path_f, sheet_name=sheet_f, usecols=region)


# get pixle size of the screen
def get_screen_size():
    hDC = win32gui.GetDC(0)
    width_f = win32print.GetDeviceCaps(hDC, win32con.DESKTOPHORZRES)
    height_f = win32print.GetDeviceCaps(hDC, win32con.DESKTOPVERTRES)
    return [width_f, height_f]


# # produce font with family and size
# def font_get(para_dict_f={"Family":None,
#                         'PointSize':None,
#                         'PixelSize':None,
#                         'Bold':None,
#                         'Italic':None,
#                         'Weight':None,
#                         'Underline':None,
#                         'LetterSpacing':None,
#                         'WordSpacing':None,
#                         'Stretch':None,
#                         'StrikeOut':None}):
#     font_f = QFont()
#     font_f.setStyleStrategy(QFont.PreferAntialias)
#     allowed_keys = ["Family", "PointSize", "Bold", "Italic", "Weight", "Underline", "StrikeOut", 
#                     "LetterSpacing", "WordSpacing", "Stretch", 'PixelSize']
#     for key, value in para_dict_f.items():
#         if (key in allowed_keys) and value:
#             dict_f = {'font_f':font_f,
#                       'value':value}
#             exec(f'font_f.set{key}(value)', dict_f)
#     return font_f


# restart python script
def restart_program(path_f):
    python_f = sys.executable
    os.execl(python_f, python_f, path_f)


# draw line plot
def lineplot_draw(
            label_datacolor_dict:dict,  # {'label':[data, color,], ...}
            x_data:list,    # [array1, array2, ...]
            x_tick:list,    # [num1, num2, ...]
            label_fillcolor_dict:dict=None, # {'label':[up_data, down_data, color], ...}
            title_all:str='',
            title_x:str='',
            title_y:str='', 
            plot_save_path='',   # absolute path demanded
            axline_list:list=[],    # [{'startpoint':int, 'color':#000000}, ...]
            ayline_list:list=[]):
    
    # set resolution of the plot
    plt.figure(figsize=(16, 9), dpi=120)  # 可选，设置图像大小

    # set title of the plot
    plt.title(title_all, fontsize=20)
    plt.xlabel(title_x, fontsize=16)
    plt.ylabel(title_y, fontsize=16)
    # set X axis label
    plt.xticks(x_tick)

    # draw vertical lines
    for dict_f in axline_list:
        plt.axvline(x=dict_f['startpoint'], color=dict_f['color'], linestyle='--')
    # draw horizatol lines
    for dict_f in ayline_list:
        plt.axhline(x=dict_f['startpoint'], color=dict_f['color'], linestyle='--')
    
    # draw line plot
    for label, data_color in label_datacolor_dict.items():
        plt.plot(x=x_data, y=data_color[0], label=label, color=data_color[1])

    # fill the area between two lines
    if label_fillcolor_dict:
        for label, up_down_color in label_fillcolor_dict.items():
            if len(up_down_color) != 3:
                color_f = label_datacolor_dict[label][1]
            else:
                color_f = up_down_color[2]
            plt.fill_between(x_data, up_down_color[0], up_down_color[1], color=color_f, alpha=0.2)

    plt.savefig(path_join(plot_save_path))
    plt.clf()