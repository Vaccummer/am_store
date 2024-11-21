import pandas as pd
from glob import glob
import webbrowser
import openpyxl
import subprocess
import os
import copy
from typing import Literal, Optional, Tuple, Union
import re
from PySide2.QtGui import QScreen
from PySide2.QtWidgets import QApplication
from PySide2.QtGui import QFont
import warnings
import math
from sympy import symbols, sympify
from am_store.common_tools import yml, AMPATH
import paramiko
import stat

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

def parse_ssh_config(file_path):
    hosts = {}
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

    return hosts

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
        dict_out = {}
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

class Config_Manager(object):
    @classmethod
    def set_shared_config(cls, config:dict):
        if not hasattr(cls, 'config'):
            cls.config = config  
    def __init__(self, 
                 wkdir:str,
                 config:dict=None, 
                 mode_name:str=None, 
                 widget_name:str=None, 
                 obj_name:str=None,
                 copy:bool=False):
        self.wkdr = wkdir
        if not hasattr(self, 'config'):
            self.config = config
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
            value_i = self.config['Common']['Size'][target_i]
            value_f = int(res_x*value_i)
            self.config['Common']['Size'][target_i] = value_f
            setattr(self, target_i, value_f)
        
        modes = ["MainWindow", "Launcher", "Searcher", "GPT"]
        for mode_i in modes:
            for key_i, value_i in self.config[mode_i]['Size'].items():
                ori = self.config[mode_i]['Size'][key_i]
                if not ori:
                    continue
                self.config[mode_i]['Size'][key_i] = self._str2int(ori)
    
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
        results = [int(sympify(expr).evalf(subs=values)) for expr in input_f]
        return results
    
    def group_chose(self, mode="_", widget="_", obj="_"):
        self.mode = mode if mode != "_" else self.mode
        self.widget = widget if widget != "_" else self.widget
        self.obj = obj if obj!="_" else self.obj
        return self
        
    def get(self, name_f, mode:str="_", widget:str="_", obj:str="_"):
        mode = mode if mode!="_" else self.mode
        widget = widget if widget!="_" else self.widget
        obj = obj if obj!="_" else self.obj
        dict_f = self.config
        for i in [mode, widget, obj, name_f]:
            if i != None:
                dict_f = dict_f.get(i, None)
                if not dict_f:
                    return None
        index_l = [name_f, mode, widget, obj]
        if "path" in index_l:
            dict_f = glob(os.path.abspath(dict_f))
            if len(dict_f) == 0:
                return None
            elif len(dict_f) == 1:
                return dict_f[0]
            else:
                return dict_f      
        elif "font" in index_l:
            return font_get(dict_f)
        else:
            return dict_f
    
    def __getitem__(self, key):
        return self.get(key)

class LauncherPathManager(object):
    def __init__(self, config:Config_Manager):
        self.config = config
        self.data_path = AMPATH(self.config.get("settings_xlsx", mode="Launcher", widget="path", obj=None))
        self.col_names= ['Name', 'Chinese Name', 'Description', 'EXE Path', "Icon_Path", 'ID', 'Group']
        self._read_xlsx()
        self.check()
    def _read_xlsx(self):
        xls = pd.ExcelFile(self.data_path)
        self.df = pd.DataFrame()
        # read all sheets and add a column to indicate the group
        for sheet_name in xls.sheet_names:
            df_t = pd.read_excel(self.data_path, sheet_name=sheet_name)
            df_t['Group'] = sheet_name
            self.df = pd.concat([self.df, df_t], ignore_index=True)
        # check the hash ID
        self.df.fillna("", inplace=True)
        self.df['ID'] = self.df.apply(lambda row: row['Name']+"-_-"+row['Chinese Name'], axis=1)
    def save_xlsx(self):
        groups = list(self.df['Group'].unique())
        with pd.ExcelWriter(self.data_path) as writer:
            for gropu_i in groups:
                self.df[self.df['Group']==gropu_i].to_excel(writer, sheet_name=gropu_i, index=False)
    def check(self):
        self.df['EXE Path'] = self.df['EXE Path'].apply(lambda x: x if os.path.exists(x) else "")
        self.df['Icon Path'] = self.df['Icon Path'].apply(lambda x: x if os.path.exists(x) else "")

class ShortcutsPathManager(object):
    def __init__(self, config:Config_Manager):
        self.config = config
        self.col_name = ["Display_Name", "Icon_Path", "EXE_Path"]
        self.data_path = AMPATH(self.config.get("setting_xlsx", mode="Launcher", widget="shortcut_setting", obj="path"))
        self._read_xlsx()
        self.check()
    def _read_xlsx(self):
        self.df = pd.read_excel(self.data_path)
    def check(self):
        self.df['EXE_Path'] = self.df['EXE_Path'].apply(lambda x: x if os.path.exists(x) else "")
        self.df['Icon_Path'] = self.df['Icon_Path'].apply(lambda x: x if os.path.exists(x) else "")
    def save(self):
        self.df.to_excel(self.data_path, index=False)

class SshManager(object):
    def __init__(self, config:Config_Manager):
        self.config = config
        self.host_config_path = self.config.get("ssh_config", "Launcher", None, "path")
        self.server=None
        self.hostname_n = None
    def _read_ssh_config(self):
        self.hosts = parse_ssh_config(self.host_config_path)
        self.hostnames = list(self.hosts.keys())

    def connect(self, host_name:str):
        try:
            assert host_name in self.hosts.keys(), f"Host name {host_name} not found in config file"
            host = self.hosts[host_name]
            self.server = paramiko.SSHClient()
            self.server.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.server.connect(host['HostName'], 
                                port=int(host.get('Port', 22)), 
                                username=host.get('User', os.getlogin()), 
                                password=host.get('Password', None))
            self.sftp = self.server.open_sftp()
            self.hostname_n = host_name
            return True
        except Exception as e:
            return e
    
    def check_connection(self):
        try:
            # 执行简单命令（例如 uptime）来检测连接
            stdin, stdout, stderr = self.server.exec_command("uptime")
            output = stdout.read().decode('utf-8')
            
            if output:
                return True
            else:
                return False
        except Exception as e:
            return False
    
    def close(self):
        self.server.close()
    
    def list_files(self, path:str):
        if not self.check_connection():
            self.connect(self.hostname_n)
        try:
            return self.sftp.listdir(path)
        except Exception as e:
            return ["Wrong Connection"]
    
    def check_exist(self, path:str):
        if not self.check_connection():
            out = self.connect(self.hostname_n)
            if out is not True:
                return False
        try:
            file_info = self.sftp.stat(path)
            if stat.S_ISDIR(file_info.st_mode):
                return 'directory'  
            else:
                return 'file'
        except Exception:
            return False
        