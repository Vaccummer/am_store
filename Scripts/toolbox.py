import pandas as pd
from glob import glob
import webbrowser
import openpyxl
import subprocess
import os
import copy
from typing import Literal, Optional, Tuple, Union, List, OrderedDict
import re
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import *
import warnings
import math
from sympy import symbols, sympify
from am_store.common_tools import yml, AMPATH
import paramiko
import stat
import asyncssh
import aiofiles
import asyncio
import pathlib
import time

def is_path(string_f, exist_check:bool=False):
    # To judge whether a variable is Path or not
    if not isinstance(string_f, str):
        return False
    if not exist_check:
        return os.path.isabs(string_f)
    else:
        return os.path.exists(string_f)

def path_format(string_f:str):
    # turn a string into a formal path of OS
    if not isinstance(string_f, str):
        raise ValueError(f"Input of path_format function should be a string, but get {type(string_f)}")
    else:
        sep = os.sep
        string_f = rf"{string_f}"
        path_t1 = string_f.replace('/', sep)
        path_t2 = path_t1.replace('\\', sep)
        return path_t2
def path_join(*args, mkdir:Literal[True, False]=True):
    # function to join str to path
    if not all(isinstance(arg, str) for arg in args):
        raise TypeError("All arguments must be of type str")
    path = os.path.join(*args)
    check_flag_f = 0
    
    pattern_f = r'^.+\.\d*[a-zA-Z]+\w*$'
    base_f = os.path.basename(path)
    
    if re.match(pattern_f, base_f):
        check_flag_f = 1
    else:
        check_flag_f = 0
    
    if mkdir:
        if check_flag_f == 0:
            os.makedirs(path, exist_ok=True)
        else:
            path_up = os.path.dirname(path)
            os.makedirs(path_up, exist_ok=True)
    return path
def web_open(url_f):
    # web lauch
    #subprocess.run(["start", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", url_f], shell=True)
    webbrowser.open(url_f)
def list_overlap(list_list_f):
    # To remove overlap of multi calsses
    return list(set.intersection(*map(set, list_list_f)))
def opto_excel_process(excel_path_f, data_f=None):
    # Read Optogenetic Setting Excel
    if not data_f:
        wb = openpyxl.load_workbook(excel_path_f, data_only=True)
        ws = wb.worksheets[0]
        empty_count_f = 0
        para_dict_f = {}
        for i_f in range(1, 10000):
            para_n = ws.cell(row=i_f, column=1).value
            para_v = ws.cell(row=i_f, column=2).value
            if empty_count_f >= 10:
                break
            if para_n and para_v:
                para_dict_f[para_n] = para_v
            else:
                empty_count_f += 1
        return para_dict_f
    else:
        wb = openpyxl.load_workbook(excel_path_f, data_only=True)
        ws = wb.worksheets[0]
        para_dict_old = {}
        empty_count_f = 0
        for i_f in range(1, 10000):
            para_n = ws.cell(row=i_f, column=1).value
            para_v = ws.cell(row=i_f, column=2).value
            if empty_count_f >= 10:
                break
            if para_n and para_v:
                para_dict_old[para_n] = i_f
            else:
                empty_count_f += 1
        for item_f, value_f in data_f.items():
            if item_f in para_dict_old.keys():
                ws.cell(row=para_dict_old[item_f], column=2, value=value_f)
        wb.save(excel_path_f)
def command_conduct(prompt_f):
    # Conduct EXE file or Open doc in Explorer
    if is_url(prompt_f):
        chrome_cmd = "start msedge --new-window " + prompt_f
        subprocess.Popen(chrome_cmd, shell=True)
    elif os.path.exists(prompt_f):
        subprocess.Popen(["explorer", prompt_f])
def rm_dp_list_elem(list_f, reverse=True):
    # To remove overlap of multi calsses, remain elements which rank upper
    a_no_duplicates = []
    if reverse:
        for i in reversed(list_f):
            if i not in a_no_duplicates:
                a_no_duplicates.insert(0, i)
    else:
        for i in list_f:
            if i not in a_no_duplicates:
                a_no_duplicates.append(i)
    return a_no_duplicates
def dir_name_sort(dir_list_f, prompt_f):
    # Sorted Association Words according to the location of prompt
    order_list = []
    for dir_f in dir_list_f:
        try:
            order_list.append([dir_f.index(prompt_f), dir_f])
        except Exception:
            order_list.append([999999, dir_f])
    return [x[1] for x in sorted(order_list, key=lambda x:x[0])]
def resize(data_f, para_dict_f, type_f):
    # resize geometry
    data_f = copy.deepcopy(data_f)
    scrx = para_dict_f['scr_x']
    scry = para_dict_f['scr_y']
    res_x = para_dict_f['res_x']
    res_y = para_dict_f['res_y']
    gap = para_dict_f['gap']
    het = para_dict_f['het']
    radius = para_dict_f['srh_r']
    win_x = para_dict_f['win_x']
    win_y = para_dict_f['win_y']
    if type_f == 'font':
        for value_if in data_f.values():
            temp_num = value_if['PixelSize']
            num_d = int(temp_num*min(res_x, res_y))
            value_if['PixelSize'] = num_d
            
    elif type_f == 'window':
        for dict_if in data_f.values():
            for key_f, value_f in dict_if.items():
                if not value_f:
                    continue
                else:
                    x, y, w, h = value_f
                    dict_t = dict()
                    exec(f'x_t=int({x})\ny_t=int({y})\nw_t=int({w})\nh_t=int({h})', locals(), dict_t)
                    dict_if[key_f] = [dict_t['x_t'], dict_t['y_t'], dict_t['w_t'], dict_t['h_t']]
    return data_f
def config_process(config_f:dict):
    ## process config file, resize and cal the geometry of windows
    # HyperSizeSet Edit
    hypersizeset = config_f['HyperSizeSet']
    scr_x, scr_y = get_screen_size()
    res_x = scr_x/2560
    res_y = scr_y/1440
    win_x = hypersizeset['win_x']
    win_y = hypersizeset['win_y']
    ## resize
    hypersizeset['gap'] = int(res_x*hypersizeset['gap'])
    hypersizeset['het'] = int(res_x*hypersizeset['het'])
    hypersizeset['srh_r'] = int(hypersizeset['srh_r']*(res_x+res_y)/2)

    gap = hypersizeset['gap']
    het = hypersizeset['het']
    srh_r = hypersizeset['srh_r']

    para_wait_for_edit = ['scr_x', 'scr_y', 'res_x', 'res_y']
    for para_if in para_wait_for_edit:
        hypersizeset[para_if] = hypersizeset[para_if] if hypersizeset[para_if] else locals()[para_if]

    # LauncherSize Edit
    hyperpara_dict = {"scr_x":scr_x, "scr_y":scr_y, "res_x":res_x, "res_y":res_y, 
                      "gap":gap, "het":het, "srh_r":srh_r, "win_x":win_x, "win_y":win_y}
    
    launchersize = config_f['LauncherSize']
    gb = {"__builtins__": None}
    lc = hyperpara_dict
    #eval_f = partial(eval, globals={"__builtins__": None}, locals=hyperpara_dict)
    for mode_name, window_geometry in launchersize.items():
        for window_name, geometry in window_geometry.items():
            if not geometry:
                continue
            x, y, w, h = str(geometry[0]), str(geometry[1]), str(geometry[2]), str(geometry[3])
            x_t, y_t, w_t, h_t = eval(x,gb,lc), eval(y,gb,lc), eval(w,gb,lc), eval(h,gb,lc)
            launchersize[mode_name][window_name] = [x_t, y_t, w_t, h_t]
    
    ## path translate
    launcher_path_set = config_f['LauncherPath']
    launcher_wkdir = path_join(config_f['Common']['work_dir'], "load")
    launcher_path_set = path_translate(launcher_path_set, launcher_wkdir)
    config_f['LauncherPath'] = launcher_path_set

    media_path_set = config_f['MediaPath']
    media_wkdir = path_join(config_f['Common']['work_dir'], "load", "player")
    media_path_set = path_translate(media_path_set, media_wkdir)
    config_f['MediaPath'] = media_path_set
    return config_f
def path_translate(path_dict_f, work_dir_f):
    path_n = dicta.flatten_dict(copy.deepcopy(path_dict_f))
    for key_f, value_f in path_n.items():
        if not value_f:
            path_l = glob(path_join(work_dir_f,*key_f[:-1], f"{key_f[-1]}.*", mkdir=False))
            path_n[key_f] = path_l[0] if path_l else None
        else:
            path_l = glob(path_join(work_dir_f, *key_f[:-1], value_f, "*", mkdir=False))
            path_n[key_f] = path_l if path_l else []
    return dicta.unflatten_dict(path_n)
def path_trans(path_dict_f, work_dir_f):
    # search for target path
    for window_ni, dict_if in path_dict_f.items():
        for key_if, value_if in dict_if.items():
            if not value_if:
                path_t = glob(os.path.join(work_dir_f, window_ni, f"{key_if}.*"))
                if len(path_t) == 1:
                    path_dict_f[window_ni][key_if] = path_t[0]
                else:
                    print(f"{window_ni}-{key_if}: No Target Detected!")
            else:
                path_t = glob(os.path.join(work_dir_f, window_ni, value_if, "*"))
                if path_t:
                    path_dict_f[window_ni][key_if] = path_t
                else:
                    print(f"{window_ni}-{value_if}: No Target Detected!")
    return path_dict_f
def nan_to_sign(list_f):
    # repalce nan with None
    return ['' if pd.isna(i) else str(i) for i in list_f]
def is_url(str_f:str):
    # judge a variable whether is a url or not
    if not isinstance(str_f, str):
        return False
    url_pattern = re.compile(
    r'^(http|https)://'  # 匹配协议部分 http:// 或 https://
    r'([a-zA-Z0-9.-]+)'  # 匹配域名部分
    r'(\.[a-zA-Z]{2,})'   # 匹配顶级域名部分
    )
    match_f = url_pattern.match(str_f)
    return bool(match_f)
def get_screen_size(target: Literal['pixel', 'physical', "dpi"]="pixel"):
    app = QApplication.instance() if QApplication.instance() else QApplication([])
    allowed_values = ["pixel", "physical","dpi"]
    assert target in allowed_values, f"Invalid value: {target}. Allowed values are: {allowed_values}"
    screen = app.primaryScreen()  # 获取主屏幕对象
    match target:
        case "pixel":
            pixel_size = screen.size()
            width_px = pixel_size.width()
            height_px = pixel_size.height()
            app.quit()
            return (width_px, height_px)
        case "physical":
            physical_size = screen.physicalSize()
            width_mm = physical_size.width()
            height_mm = physical_size.height()
            app.quit()
            return [width_mm, height_mm]
        case "dpi":
            app.quit()
            return screen.physicalDotsPerInch()
def excel_to_df(excel_path_f:str, region:str, sheet_name_f:Union[int, str, list]='Sheet1'):  
    # Read XLSX doc and transform it into dataframe
    # region format : 'A1:Z7'
    # sheet_name_f : Sheet name or Sheet order number(start from 1)
    import pandas as pd
    assert is_path(excel_path_f, exist_check=True), f"Invalid path: {excel_path_f}. PATH NOT EXISTS!"
    try:
        dataframe_f = []
        if sheet_name_f == "all":
            workbook = openpyxl.load_workbook(excel_path_f)
            sheet_name_f = workbook.sheetnames
        if isinstance(sheet_name_f, list):
            for sheet_i in sheet_name_f:
                dataframe_i = pd.read_excel(excel_path_f, sheet_name=sheet_i, usecols=region)
                dataframe_f.append(dataframe_i)
            dataframe_f = pd.concat(dataframe_f, ignore_index=True)
        else:
            dataframe_f = pd.read_excel(excel_path_f, sheet_name=sheet_name_f, usecols=region)
    except Exception as e:
        dataframe_f = None
        warnings.warn(f"excel_to_df('{excel_path_f}') encounter error {e}, return None in default")
    return dataframe_f

def font_get(para_dict_f={"Family":None,
                        'PointSize':None,
                        'PixelSize':None,
                        'Bold':None,
                        'Italic':None,
                        'Weight':None,
                        'Underline':None,
                        'LetterSpacing':None,
                        'WordSpacing':None,
                        'Stretch':None,
                        'StrikeOut':None}):
    # produce font with family and size
    font_f = QFont()
    font_f.setStyleStrategy(QFont.PreferAntialias)
    allowed_keys = ["Family", "PointSize", "Bold", "Italic", "Weight", "Underline", "StrikeOut", 
                    "LetterSpacing", "WordSpacing", "Stretch", 'PixelSize']
    for key, value in para_dict_f.items():
        if (key in allowed_keys) and value:
            dict_f = {'font_f':font_f,
                      'value':value}
            exec(f'font_f.set{key}(value)', dict_f)
    
    return font_f

def parse_ssh_config(file_path, fliter:Literal['all'] | None | List[str]):
    hosts = {}
    try:
        with open(file_path, 'r') as file:
            current_host = None
            host_config = {}
            for line in file:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if line.lower().startswith('host '):
                    if current_host:
                        hosts[current_host] = host_config
                    current_host = line.split()[1]
                    host_config = {}
                    continue
                match = re.match(r'(\w+)\s+(.+)', line)
                if match:
                    key, value = match.groups()
                    host_config[key] = value
            if current_host:
                hosts[current_host] = host_config
        if fliter == 'all':
            return hosts
        elif fliter is None:
            return {}
        else:
            dict_t = {}
            for name_i in fliter:
                host_i = hosts.get(name_i, None)
                if host_i is not None:
                    dict_t[name_i] = host_i
            return dict_t
    except Exception as e:
        return {}

def amlayoutH(align_h:Literal['l','r','c']=None, align_v:Literal['t','b','c']=None, spacing:int=None)->QHBoxLayout:
    lo = QHBoxLayout()
    match align_h:
        case 'l':
            lo.setAlignment(Qt.AlignLeft)
        case "c":
            lo.setAlignment(Qt.AlignHCenter)
        case "r":
            lo.setAlignment(Qt.AlignRight)
        case _:
            pass
    match align_v:
        case "t":
            lo.setAlignment(Qt.AlignTop)
        case "b":
            lo.setAlignment(Qt.AlignBottom)
        case "c":
            lo.setAlignment(Qt.AlignVCenter)
    if spacing:
        lo.setSpacing(int(spacing))
    return lo
def amlayoutV(align_h:Literal['l','r','c']=None, align_v:Literal['t','b','c']=None, spacing:int=None)->QVBoxLayout:
    lo = QVBoxLayout()
    match align_h:
        case 'l':
            lo.setAlignment(Qt.AlignLeft)
        case "c":
            lo.setAlignment(Qt.AlignHCenter)
        case "r":
            lo.setAlignment(Qt.AlignRight)
        case _:
            pass
    match align_v:
        case "t":
            lo.setAlignment(Qt.AlignTop)
        case "b":
            lo.setAlignment(Qt.AlignBottom)
        case "c":
            lo.setAlignment(Qt.AlignVCenter)
    if spacing:
        lo.setSpacing(int(spacing))
    return lo

def add_obj(*args, parent_f:Union[QHBoxLayout, QVBoxLayout]):
    for arg_i in args:
        if isinstance(arg_i, QHBoxLayout):
            parent_f.addLayout(arg_i)
        elif isinstance(arg_i, QVBoxLayout):
            parent_f.addLayout(arg_i)
        else:
            parent_f.addWidget(arg_i)
    return parent_f




class dicta:
    @staticmethod
    def flatten_dict(dict_f:dict):
        # flatten dict, keys of multi layers stored in tuple
        sep_f = "$==>>$"
        def flatten_dict_core(d, parent_key='', sep=sep_f):
            items = []
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(flatten_dict_core(v, new_key, sep=sep).items())
                else:
                    items.append((new_key, v))
            return dict(items)
        dict_ori = flatten_dict_core(dict_f)
        dict_out = OrderedDict()
        for key, value in dict_ori.items():
            key_list = key.split(sep_f)
            dict_out[tuple(key_list)] = value
        return dict_out
    
    @staticmethod
    def edit(dict_f:dict, edit_info:dict, force=False):
        # edit_info can be common dict or flatten dict(keys stored in tuple)
        edit_info_format = {}
        for key_i, value_i in edit_info.items():
            if isinstance(key_i, tuple):
                edit_info_format[key_i] = value_i
            else:
                edit_info_format.update(dicta.flatten_dict({key_i:value_i}))
        
        if not force:
            for key_tuple, value in edit_info_format.items():
                if len(key_tuple) == 1:
                    if dict_f.get(key_tuple[0]):
                        dict_f[key_tuple[0]] = value
                    continue
                sign_f = True
                for index_f, key in enumerate(key_tuple[:-1]):
                    if index_f == 0:
                        if not dict_f.get(key):
                            sign_f = False
                            break
                        else:
                            data_n = dict_f[key]
                    else:
                        if data_n.get(key):
                            data_n = data_n[key]
                        else:
                            sign_f = False
                            break
                if sign_f:
                    data_n[key_tuple[-1]] = value    
        else:
            for key_tuple, value in edit_info_format.items():
                if len(key_tuple) == 1:
                    dict_f[key_tuple[0]] = value
                    continue
                for index_f, key in enumerate(key_tuple[:-1]):
                    if index_f == 0:
                        if not dict_f.get(key):
                            dict_f[key] = {}
                        data_n = dict_f[key]
                    else:
                        if not data_n.get(key):
                            data_n[key] = {}
                        data_n = data_n[key]
                data_n[key_tuple[-1]] = value
        return data_n

class SSHConductor(object):
    def __init__(self, sftp:Union[paramiko.SFTPClient]):
        self.sftp = sftp
    
    def check_path(self, path:str):
        try:
            file_info = self.sftp.stat(path)
            return {
                "connect": True,
                "exist": True,
                "mode": self.get_path_type(file_info.st_mode),
                "size": file_info.st_size,
                }
        except FileNotFoundError:
            return {
                "connect": True,
                "exist": False,
                "mode": None,
                "size": None,
                }
        except Exception as e:
            return {
                "connect": False,
                "exist": None,
                "mode": None,
                "size": None,
                "error": e
                }

    def list_dir(self, path:str):
        check_d = self.check_path(path)
        if not (check_d['connect'] or check_d['exist']):
            return []
        if check_d['mode'] != "dir":
            return []
        try:
            dirs = self.sftp.listdir(path)
            return dirs
        except Exception as e:
            return []
    
    def get_path_type(self, st_mode):
        if stat.S_ISDIR(st_mode):
            return "dir"
        elif stat.S_ISREG(st_mode):
            return "file"
        elif stat.S_ISLNK(st_mode):
            return "link"
        else:
            return "unknown"


class Config_Manager(object):
    @classmethod
    def set_shared_config(cls, config:dict):
        if not hasattr(cls, 'config'):
            cls.config = dicta.flatten_dict(config)
    
    def __init__(self, 
                 wkdir:str,
                 config:dict=None, 
                 mode_name:str=None, 
                 widget_name:str=None, 
                 obj_name:str=None,
                 copy:bool=False):
        self.wkdr = wkdir
        self.set_shared_config(config)
        self.mode = mode_name
        self.widget = widget_name
        self.obj = obj_name
        if not copy:
            self._calculate_size()
    
    def deepcopy(self):
        new_copy = Config_Manager(self.wkdr, self.config, None, None, None, True)
        return new_copy
    
    def _calculate_size(self):
        self.scr_x, self.scr_y = get_screen_size('pixel')
        res_x = math.sqrt(self.scr_x*self.scr_y/(2560*1600))
        res_y = res_x
        # resize 
        targets = ['win_x', "win_y", "gap", "het", "srh_r"]
        for target_i in targets:
            value_i = self.config[('Common','Size',target_i)]
            value_f = int(res_x*value_i)
            self.config[('Common','Size',target_i)] = value_f
            setattr(self, target_i, value_f)
        
        for key_i, value_i in self.config.items():
            if "Size" in key_i:
                self.config[key_i] = self._str2int(value_i)

    def _str2int(self, input_f:Union[list, str]):
        scr_x, scr_y, win_x, win_y, gap, het, srh_r= symbols('scr_x scr_y win_x win_y gap het srh_r')
        values = {
                scr_x: self.scr_x,
                scr_y: self.scr_y,
                win_x: self.win_x,
                win_y: self.win_y,
                gap: self.gap,
                het: self.het,
                srh_r:self.srh_r,
                }
        if isinstance(input_f, list):
            results = [int(sympify(expr).evalf(subs=values)) for expr in input_f]
            return results
        elif isinstance(input_f, str):
            return int(sympify(input_f).evalf(subs=values))
        else:
            return input_f
    
    def group_chose(self, mode="_", widget="_", obj="_"):
        self.mode = mode if mode != "_" else self.mode
        self.widget = widget if widget != "_" else self.widget
        self.obj = obj if obj!="_" else self.obj
        return self
        
    def get(self, name_f:str, mode:str="_", widget:str="_", obj:str="_", default_v='^default_for_get_func$',ae:bool=True):
        mode = mode if mode!="_" else self.mode
        widget = widget if widget!="_" else self.widget
        obj = obj if obj!="_" else self.obj
        args_a = [i for i in [mode, widget, obj, name_f] if i != None]
        if default_v != '^default_for_get_func$':
            out_a = self.config.get(tuple(args_a), default_v)
        else:
            out_a = self.config.get(tuple(args_a), None)
            if out_a is None:
                return out_a
        if ae:
            return self.after_process(args_a, out_a)
        else:
            return out_a
    
    def __getitem__(self, key):
        if isinstance(key, tuple):
            out_a = self.config.get(key, None)
            if out_a is None:
                return out_a 
            else:
                return self.after_process(key, out_a)
        else:
            return self.get(key)

    def after_process(self, args_a:tuple, target_f):
        if "path" in args_a:
            if isinstance(target_f, list):
                out_l = []
                for i in target_f:
                    if os.path.isabs(i):
                        out_l.append(i)
                    else:
                        out_l.append(str((pathlib.Path(self.wkdr)/pathlib.Path(i)).resolve()))
                return out_l
            elif isinstance(target_f, str):
                if os.path.isabs(target_f):
                    return target_f
                else:
                    return str((pathlib.Path(self.wkdr)/pathlib.Path(target_f)).resolve())
            else:
                return target_f
        elif "font" in args_a:
            font_dict = {i[0]:i[1] for i in target_f}
            return font_get(font_dict)
        else:
            return target_f

class LauncherPathManager(object):
    def __init__(self, config:Config_Manager):
        self.config = config
        self.data_path = AMPATH(self.config.get("settings_xlsx", mode="Launcher", widget="path", obj=None))
        self.permit_col = ['Name', 'Chinese Name', 'EXE Path']

        self.conduct_l = []
        self.name = 'PathManager'
        self.sign_for_separate = self.config.get('separate_sign', 'Settings', self.name)
        disallowed_chars_pattern = r'[<>:"/\\|?*]'
        if (not self.sign_for_separate) or re.findall(disallowed_chars_pattern, self.sign_for_separate):
            self.sign_for_separate = "^--$"
        self._read_xlsx()
        self.check()
        self._load_icon_dict()
    
    def _read_xlsx(self):
        self.df = OrderedDict()
        with pd.ExcelFile(self.data_path) as xls:
            # read all sheets and add a column to indicate the group
            for sheet_name in xls.sheet_names:
                df_t = pd.read_excel(self.data_path, sheet_name=sheet_name)
                for col_i in df_t.columns:
                    if col_i not in self.permit_col:
                        df_t.drop(col_i, axis=1, inplace=True)
                df_t.dropna(axis=0, how='all', inplace=True)
                df_t.fillna("", inplace=True)
                self.df[sheet_name] = df_t
        self.total_name_d = {}
        self.total_names = []
        for name_i, df_i in self.df.items():
            self.total_name_d[name_i] = df_i['Name'].to_list()
            self.total_names.extend(df_i['Name'].to_list())
        return self.df

    def save_xlsx(self):
        with pd.ExcelWriter(self.data_path, mode='w') as writer:
            for name_i, df_i in self.df.items():
                df_i.to_excel(writer, sheet_name=name_i, index=False)
    
    def check(self):
        for name_i, df_i in self.df.items():
            self.df[name_i]['EXE Path'] = self.df[name_i]['EXE Path'].apply(lambda x: x if os.path.exists(x) else "")
        #self.df['EXE Path'] = self.df['EXE Path'].apply(lambda x: x if os.path.exists(x) else "")
    
    def _load_icon_dict(self):
        self.default_app_icon_path = self.config.get('default_app_icon', mode="Launcher", widget='associate_list', obj="path")
        self.default_app_icon = QIcon(self.default_app_icon_path)
        self.app_icon_folder = self.config.get('app_icon_folder', mode="Launcher", widget='associate_list', obj="path")
        self.app_icon_d = {name:{} for name in self.df.keys()}
        for name_i in os.listdir(self.app_icon_folder):
            path_i = os.path.join(self.app_icon_folder, name_i)
            if os.path.isfile(path_i):
                group_name, ext = os.path.splitext(name_i)
                tmp_l = group_name.split(self.sign_for_separate)
                if len(tmp_l) <= 1:
                    continue
                else:
                    group, app_name = tmp_l[:2]
                if app_name in self.app_icon_d[group].keys():
                    warnings.warn(f"Icon for {app_name} in group {group} already exists, skip {path_i}")
                else:
                    self.app_icon_d[group][app_name] = path_i
        self.exe_icon_getter = self.config.get('exe_icon_getter', mode="Launcher", widget='associate_list', obj="path").replace('\\', '/')
    
    def get_icon(self, name:str, group:str=None)->QIcon:
        if group:
            icon_l = self.app_icon_d[group].get(name, "")
        else:
            icon_l = ""
            for group_i, app_d in self.app_icon_d.items():
                icon_l = app_d.get(name, "")
                if icon_l:
                    group = group_i
                    break
        if icon_l:
            return QIcon(icon_l)
        else:
            if not group:
                return QIcon(self.default_app_icon)
            exe_t = self.df[group][self.df[group]['Name']==name]
            if len(exe_t) == 0:
                return self.default_app_icon
            exe_t = exe_t.iloc[0]['EXE Path']
            name_t = group+self.sign_for_separate+name
            target_icon_path = os.path.join(self.app_icon_folder, name_t).replace('\\', '/')
            if exe_t.endswith('.exe') and (name not in self.conduct_l):
                self.conduct_l.append(name)
                commands_f = [self.exe_icon_getter, exe_t, target_icon_path+'.png']
                result = subprocess.check_output(commands_f, cwd=os.path.dirname(self.exe_icon_getter)).decode('gbk')
                if result and "图标已保存为" in result:
                    self.app_icon_d[group][name] = (target_icon_path+'.png').replace('/', '\\')
                    return QIcon(target_icon_path+'.png')
                else:
                    self.app_icon_d[group][name] = self.default_app_icon_path
                    return self.default_app_icon               
            else:
                self.app_icon_d[group][name] = self.default_app_icon_path
                return self.default_app_icon

class ShortcutsPathManager(object):
    def __init__(self, config:Config_Manager):
        self.config = config
        self.col_name = ["Display_Name", "Icon_Path", "EXE_Path"]
        self.data_path = AMPATH(self.config.get("setting_xlsx", mode="Launcher", widget="shortcut_obj", obj="path"))
        self._read_xlsx()
        self.check()
        self._load()
    
    def _read_xlsx(self):
        self.df = pd.read_excel(self.data_path)
        self.df.fillna("", inplace=True)
    
    def check(self):
        self.df['EXE_Path'] = self.df['EXE_Path'].apply(lambda x: x if is_path(x, exist_check=True) else "")
        self.df['Icon_Path'] = self.df['Icon_Path'].apply(lambda x: x if is_path(x, exist_check=True) else "")
    
    def _load(self):
        self.icon_dir = AMPATH(self.config.get("button_icons", mode="Launcher", widget="shortcut_obj", obj="path"))
        self.icon_dict = {}
        for path_i in self.icon_dir.iterdir():
            if path_i.is_dir():
                continue
            name_i = path_i.stem
            self.icon_dict[name_i] = str(path_i)
        self.default_icon = QIcon(self.config.get("default_button_icon", mode="Launcher", widget="shortcut_obj", obj="path"))
        self.conduct_l = []
        self.exe_icon_getter = self.config.get('exe_icon_getter', mode="Launcher", widget='associate_list', obj="path").replace('\\', '/')
    
    def geticon(self, name:str, str_format:bool=False)->QIcon:
        path_t = self.icon_dict.get(name, "")
        if path_t:
            if str_format:
                return path_t
            else:
                return QIcon(path_t)
        else:
            exe_paths = self.df[self.df['Display_Name']==name]['EXE_Path'].values
            if not exe_paths:
                if str_format:
                    return self.default_icon
                else:
                    return QIcon(self.default_icon)
            exe_path = exe_paths[0]
            if exe_path.endswith('.exe')and (name not in self.conduct_l):
                target_icon_path = os.path.join(self.icon_dir, name).replace('\\', '/')
                commands_f = [self.exe_icon_getter, exe_path, target_icon_path+'.png']
                result = subprocess.check_output(commands_f, cwd=os.path.dirname(self.exe_icon_getter)).decode('gbk')
                self.conduct_l.append(name) 
                if result and "图标已保存为" in result:
                    self.icon_dict[name] = (target_icon_path+'.png').replace('/', '\\')
                    if str_format:
                        return target_icon_path+'.png'
                    else:
                        return QIcon(target_icon_path+'.png')
                else:
                    self.icon_dict[name] = self.default_icon
                    if str_format:
                        return self.default_icon
                    else:
                        return QIcon(self.default_icon)     
            else:
                self.icon_dict[name] = self.default_icon
                if str_format:
                    return self.default_icon
                else:
                    return QIcon(self.default_icon) 
                          
    def save(self):
        self.df.to_excel(self.data_path, index=False)

class SshManager(object):
    def __init__(self, parent:QMainWindow, config:Config_Manager):
        self.up = parent
        self.config = config.deepcopy()
        self.config.group_chose(mode='Settings', widget='SSHConfig', obj=None)
        self.server=None
        self.sftp = None
        self.hostname_n = None
        self.host = []
        self.stop_check = False
        self.sleep_state = True
        self._load_config()
    
    def _load_config(self):
        self.host_config_path = self.config.get("ssh_config")
        if not self.host_config_path:
            self.host_config_path = os.path.expanduser("~/.ssh/config")
        if os.path.exists(self.host_config_path):
            self.hosts = parse_ssh_config(self.host_config_path,
                                        fliter=self.config.get("hostname"))
        else:
            self.up.tip("Warning", "SSH config file not found, please check the path", {"OK":""}, "")
            self.hosts = {}
        self.wsl_l = self.config.get("wsl")
        self.wsl_d = {i[0]:{'path':i[1], 'user':i[2]} for i in self.wsl_l}
        self.hostd = {'Local':''} | self.wsl_d | self.hosts
        self.hostnames = list(self.hostd.keys())
        self.host_type = {'Local':'Local'} | {i:"WSL" for i in self.wsl_d.keys()} | {i:"Remote" for i in self.hosts.keys()}
    
    def get_config(self, name:str):
        assert name in self.hostd.keys(), f"Invalid host name: {name}"
        type_t = self.host_type[name]
        config_t = self.hostd[name]
        return {'type':type_t, 'config':config_t}



    def check_connection(self):
        if self.up.CONNECT:
            return True
        else:
            match self.up.CONNECT:
                case None:
                    self.up.tip("Warning", "No connection established yet", {"OK":""}, "")
                case False:
                    self.up.tip("Error", f"Connection failed, error info {self.up.CON_ERROR}", {"OK":""}, "")
                case _:
                    self.up.tip("Error", "Unknown Error", {"OK":""}, "")
        return False
    
    def close(self):
        self.server.close()
    
    def list_files(self, path:str):
        if not self.check_connection():
            return
        try:
            return self.sftp.listdir(path)
        except Exception as e:
            return ["Wrong Connection"]
    
    def check_exist(self, path:str):
        if not self.check_connection():
            self.up.refresh_connect()
            return "False"
        try:
            file_info = self.sftp.stat(path)
            if stat.S_ISDIR(file_info.st_mode):
                return 'directory'  
            else:
                return 'file'
        except Exception:
            return 'False'
    
    def walk(self, src:str):
        file_info = []
        def list_files(path):
            try:
                dir_contents = self.sftp.listdir_attr(path)
                for entry in dir_contents:
                    relative_path = os.path.relpath(path + '/' + entry.filename, start=src)
                    if entry.st_mode & 0o170000 == 0o040000:  # 判断是否是目录
                        file_info.append((relative_path, 'directory', 0))
                        list_files(path + '/' + entry.filename)
                    else:
                        file_info.append((relative_path, 'file', entry.st_size))
            except Exception as e:
                print(f"Error accessing path {path}: {e}")
        # 从 src 目录开始递归遍历
        list_files(src)
        return file_info
    
    def getsize(self, src:str):
        try:
            return self.sftp.stat(src).st_size
        except Exception as e:
            return 0

class WorkerThread(QThread):
    finished_signal = Signal(list)
    def __init__(self, function:callable, *args:tuple, **kwargs:dict):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs
    def run(self):
        try:
            out = self.function(*self.args, **self.kwargs)
            self.finished_signal.emit([True, out])
        except Exception as e:
            self.finished_signal.emit([False, str(e)])

class ConnectionMaintainer(QThread):
    data_updated = Signal(dict)
    output = Signal(list)
    @Slot(list)
    def update_data(self, data:dict):
        # tuple: [host_name:str, host_d, host_type:str, connection_state]
        self.host_name = data['HOST']
        self.host_config = data['host_config']
        self.host_type = data['HOST_TYPE']
        self.state = data['CONNECT']
        
    def __init__(self, config:Config_Manager):
        super().__init__()
        self.config = config.deepcopy().group_chose(mode='Settings', widget='SSHConfig',)
        self.data_updated.connect(self.update_data)
        self.update_data({'HOST':'Local', 'host_config':{}, 'HOST_TYPE':'Local', 'CONNECT':True})
        self.close_sign = False
    
    def _connect(self) ->list:
        self.server = paramiko.SSHClient()
        self.server.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.server.connect(self.host_config['HostName'], 
                                port=self.host_config.get('port', 22), 
                                username=self.host_config.get('User', os.getlogin()), 
                                password=self.host_config.get('Password', ''),
                                timeout=3)
            self.sftp = self.server.open_sftp()
            return [True, [self.host_name, self.sftp]]
        except Exception as e:
            return [False, str(e)]

    def run(self):
        while True:
            if self.close_sign:
                break
            if self.host_type != 'Remote':
                time.sleep(0.1)
                continue
            else:
                if self.state:
                    time.sleep(0.1)
                    continue
                else:
                    out = self._connect()
                    self.output.emit(out)

    def stop(self):
        self.close_sign = True

class TransferMaintainer(QThread):
    bar_state = Signal(list)    # output the state and progress of the transfer
    stop_signal = Signal(bool)  # stop the transfer
    def __init__(self,config:Config_Manager):
        super().__init__()
        self.name = "TransferMaintainer"
        self.config = config.deepcopy().group_chose(mode='Settings', widget=self.name,obj=None)
        self._load()
    
    def _load(self):
        self.local_min_chunck = self.config.get('local_min_chunck')*1024**2
        self.local_max_chunck = self.config.get('local_max_chunck')*1024**2
        self.remote_min_chunck = self.config.get('remote_min_chunck')*1024**2
        self.remote_max_chunck = self.config.get('remote_max_chunck')*1024**2
        self.task_queue = []
        self.loop = None  # Event loop for asyncio
        self.state = 'Stop'
    
    def _load_task(self, task:List[dict]):
        self.task_queue.extend(task)
    
    def worker_func(self, data:dict):
        connect_type = data['connect_type']
        task_type = data['task_type']
        paras_old = data['paras'] # [[src, dst, size, type], [src, dst, size, type]]
        paras_new = []
        new_config = {}
        if connect_type == 'remote':
            connect_config = data.get('connect_config', None)
            if not connect_config:
                return
            new_config['host'] = connect_config['HostName']
            new_config['port'] = connect_config.get('port', 22)
            new_config['username'] = connect_config.get('User', os.getlogin())
            new_config['password'] = connect_config.get('Password', '')
            new_config['timeout'] = 3
        for para_i in paras_old:
            src, dst, size, file_type_t = para_i
            size_f = int(size)
            chunk_size = self.cal_chunck_size(size_f, connect_type)
            paras_new.append({'src':src, 'dst':dst, 'size':size_f, 'chunk_size':chunk_size, 
                              'connect_type':connect_type, 'task_type':task_type, 'file_type':file_type_t, 
                              'config':new_config})
    
    def run(self):
        self.loop = asyncio.new_event_loop()  # Create a new event loop
        asyncio.set_event_loop(self.loop)  # Bind loop to current thread
        count_i = 0
        while True:
            if self.task_queue:
                data_i = self.task_queue.pop(0)
                continue
            time.sleep(0.1)
            if count_i % 10 == 0:
                self.bar_state.emit([False, 0])
            self.stop_signal.emit(True)
    

    def progress_update(self, updated_progress:int):
        self.total_progress += updated_progress
        self.bar_state.emit([True, self.total_progress/self.total_size])
    
    def cal_chunck_size(self, size_f:int, hosttype:Literal['local', 'remote'])->int:
        if hosttype == 'local':
            tar_size = min(max(self.local_min_chunck, size_f//48), self.local_max_chunck, size_f)
            return tar_size
        else:
            tar_size = min(max(self.remote_min_chunck, size_f//48), self.remote_max_chunck, size_f)
            return tar_size
    
    async def copy_file_chunk(self, src:str, dst:str, chunk_size:int, 
                              connect_type:Literal['local', 'remote'], 
                              task_type:Literal['upload', 'download'],
                              file_type:Literal['file', 'dir']):
        async with aiofiles.open(src, 'rb') as fsrc, aiofiles.open(dst, 'wb') as fdst:
            while True:
                chunk = await fsrc.read(chunk_size)
                if not chunk:
                    break  
                await fdst.write(chunk)
                self.progress_update(chunk_size)
    
    def stop(self):
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
        self.quit()
        self.wait()


import asyncio
import asyncssh
from typing import List, Literal

class FileTransfer:
    def __init__(self, remote_server):
        self.remote_server = remote_server

    async def transfer_single_file(self, src: str, dst: str, sftp, type_f: Literal['get', 'put'], semaphore: asyncio.Semaphore):
        async with semaphore:  # 限制并发数
            if type_f == 'get':
                await sftp.get(src, dst)  # 下载文件
            elif type_f == 'put':
                await sftp.put(src, dst)  # 上传文件
            print(f"{type_f} file from {src} to {dst} completed.")

    async def transfer_multiple_files(self, tasks: List[tuple[str, str]], type_f: Literal['get', 'put'], max_connections: int = 5):
        host_d = self.remote_server.host
        semaphore = asyncio.Semaphore(max_connections)  # 最大并发数

        try:
            async with asyncssh.connect(host_d['HostName'], 
                                        username=host_d.get('User', os.getlogin()), 
                                        password=host_d.get(('Password', '')),
                                        port=int(host_d.get('port', 22))) as conn:
                async with conn.start_sftp_client() as sftp:
                    transfer_tasks = []  
                    for src, dst in tasks:
                        transfer_tasks.append(self.transfer_single_file(src, dst, sftp, type_f, semaphore))
                    await asyncio.gather(*transfer_tasks)
                    return True
        except Exception as e:
            print(f"文件传输失败: {e}")
            return False
