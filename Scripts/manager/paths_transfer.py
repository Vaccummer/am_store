from PySide2.QtWidgets import QMainWindow
from PySide2.QtGui import QIcon
from PySide2.QtCore import Signal, Slot, QObject
from Scripts.tools.toolbox import *
from Scripts.manager.config_ui import AIcon
import Scripts.global_var as GV
import numpy as np
from typing import *
from Scripts.manager.config_ui import Config_Manager  
from Scripts.manager.config_ui import UIUpdater
import clr
from PIL import Image
from PIL.Image import Image as ImageType
import io
import pickle
from datetime import datetime
import hashlib
clr.AddReference(os.path.abspath("./Scripts/manager/IconExtractor.dll"))
from IconExtractor import Worker    # type: ignore
import shutil

class IconSet:
    def __init__(self, path:str, icon:QIcon):
        pass

class LauncherPathManager(QObject):
    xlsx_save_signal = Signal()
    icon_save_signal = Signal(GV.IconSaveRequest)

    def __init__(self, config:Config_Manager):
        super().__init__()
        self.config = config
        self._loadAll()

    def _loadAll(self):
        self.save_signal.connect(self.save2xlsx)
        self.icon_save_signal.connect(self.app_icon_save)
        self.data_path = UIUpdater.get(atuple('Manager', 'LauncherPathManager', 'path', 'settings_xlsx_path'), './load/Manager/LauncherPathManager/settings.xlsx')
        self.permit_col = ['Name', 'Chinese Name', 'EXE Path'] 
        self.conduct_l = []
        self.name = 'PathManager'
        self.sign_for_separate = self.config.get('separate_sign', 'Settings', self.name)
        disallowed_chars_pattern = r'[<>:"/\\|?*]'
        if (not self.sign_for_separate) or re.findall(disallowed_chars_pattern, self.sign_for_separate):
            self.sign_for_separate = "^--$"
        self.df_app_ptr = atuple('Manager', 'LauncherPathManager', 'path', 'default_app_icon')
        self.df_file_ptr = atuple('Manager', 'LauncherPathManager', 'path', 'default_file_icon')
        self.df_folder_ptr = atuple('Manager', 'LauncherPathManager', 'path', 'default_folder_icon')
        self.extractor_record:dict[str:bool] = {}
        self.icon_cache_folder = UIUpdater.get(atuple('Manager', 'LauncherPathManager', 'path', 'icon_cache_folder'), 
                                               './load/Manager/LauncherPathManager/icon_cache')
        UIUpdater.set(alist(self.df_app_ptr, self.df_file_ptr, self.df_folder_ptr), self._load_default_icon, alist())   
        self._load_app_info()
        self._load_icon_dict()
        self.auto_get_icon()
        
    def _load_default_icon(self, df_app:str, df_file:str, df_folder:str):
        self.default_app_icon = AIcon(df_app) if df_app else AIcon()
        self.default_file_icon = AIcon(df_file) if df_file else AIcon()
        self.default_folder_icon = AIcon(df_folder) if df_folder else AIcon()

    def _load_icon_dict(self)->None:
        # load icon path for app_d
        '''
        icons are stored in the folder as {group}{self.sign_for_separate}{app_name}.png, like Launcher--$Notepad.png
        '''
        self.app_icon_folder = UIUpdater.get(atuple('Manager', 'LauncherPathManager', 'path', 'app_icon_folder'), './load/Launcher/app_icons')
        for name_i in os.listdir(self.app_icon_folder):
            path_i = os.path.join(self.app_icon_folder, name_i)
            if not self.check_format(path_i):
                continue
            group, app_name = os.path.splitext(name_i)[0].split(self.sign_for_separate)
            if not all([group, app_name]):
                os.remove(path_i)
                continue
            if self.app_d.get(app_name, None):
                self.app_d[app_name].icon_path = path_i
            else:
                os.remove(path_i)
        
        # load icon path for common file_icon_d
        '''
        icons are stored in the folder as {ext_name}.png, like txt.png, jpg.png, etc.
        '''
        self.file_icon_folder = UIUpdater.get(atuple('Manager', 'LauncherPathManager', 'path', 'file_icon_folder'), '')
        self.file_icon_d:dict[str,AIcon] = {}
        for name_i in os.listdir(self.file_icon_folder):
            path_i = os.path.join(self.file_icon_folder, name_i)
            if not self.check_format(path_i):
                continue
            ext_name = os.path.splitext(name_i)[0]
            self.file_icon_d[f'.{ext_name}'] = AIcon(path_i)
        
        # load icon path for folder_icon_d
        '''
        icons are stored in the folder as {hash_num}.png, like 1234567890.png, hash_num is the hash of tuple(host, path)
        '''
        self.folder_icons = UIUpdater.get(atuple('Manager', 'LauncherPathManager', 'path', 'folder_icon_folder'), 
                                               './load/Manager/LauncherPathManager/folder_icons')
        self.folder_icon_d:dict[str, AIcon] = {}
        for name_i in os.listdir(self.folder_icons):
            path_i = os.path.join(self.folder_icons, name_i)
            if not self.check_format(path_i):
                continue
            hash_num = os.path.splitext(name_i)[0]
            self.folder_icon_d[hash_num] = AIcon(path_i)
        
        # load icon path for exe_file_icon_d
        '''
        icons are stored in the folder as {hash_num}.png, like 1234567890.png, hash_num is the hash of tuple(host, exe_path)
        '''
        self.exe_file_icon_folder = UIUpdater.get(atuple('Manager', 'LauncherPathManager', 'path', 'exe_file_icon_folder'), '')
        self.exe_file_icon_d:dict[str, AIcon] = {}
        for name_i in os.listdir(self.exe_file_icon_folder):
            path_i = os.path.join(self.exe_file_icon_folder, name_i)
            name_r = os.path.splitext(name_i)[0]
            if not self.check_format(path_i):
                continue
            self.exe_file_icon_d[name_r] = AIcon(path_i)
    
    def _load_app_info(self)->None: 
        self.app_d:dict[str:GV.LauncherAppInfo] = {}
        with pd.ExcelFile(self.data_path) as xls:
            # read all sheets and add a column to indicate the group
            for sheet_name in xls.sheet_names:
                df_t = pd.read_excel(self.data_path, sheet_name=sheet_name)
                df_t.dropna(axis=0, how='all', inplace=True)
                df_t.fillna("", inplace=True)
                for row_i in df_t.iterrows():
                    row_d = row_i[1].to_dict()
                    name_i = row_d['Name']
                    chname_i = row_d['Chinese Name']
                    group_i = sheet_name
                    exe_path_i = row_d['EXE Path']
                    exe_path_i = exe_path_i if is_path(exe_path_i, exist_check=True) else ""
                    ID_f = self.hash_app(name_i, group_i)
                    self.app_d[name_i] = GV.LauncherAppInfo(ID=ID_f, name=name_i, chname=chname_i, group=group_i, exe_path=exe_path_i)

    def auto_get_icon(self):
        for app_i in self.app_d.values():
            path_t = link2path(app_i.exe_path)
            if is_path(path_t, exist_check=True) and os.path.splitext(path_t)[1].lower() in ['.exe', '.dll']:
                icon_path = self.app_icon_extract(path_t, app_i.group, app_i.name)
                if icon_path:
                    app_i.icon_path = icon_path

    def check_format(self, name_i:str)->bool:
        check_file = is_path(name_i, exist_check=True)
        check_ext = os.path.splitext(name_i)[1] in ['.png', '.svg', '.ico', 'jpg', 'jpeg', 'bmp']
        return check_file and check_ext
        
    def extract_exe_icon(self, exe_path:str, index_f:int=0)->ImageType|None:
        exe_path = link2path(exe_path)
        if os.path.splitext(exe_path)[1].lower() not in ['.exe','dll']:
            return None
        try:
            image_data = Worker.Extract(exe_path, index_f)
            image_f = Image.open(io.BytesIO(image_data))
            return image_f
        except Exception as e:
            #warnings.warn(f"Error extracting icon from {exe_path}: {e}")
            return None

    def app_icon_extract(self, exe_path:str, group:str, name:str, index_f:int=0)->str|None:
        if self.extractor_record.get((exe_path, group, name), False):
            return None
        image_f = self.extract_exe_icon(exe_path, index_f)
        if image_f is None:
            return None
        dst_name = f"{group}{self.sign_for_separate}{name}.png"
        dst_path = os.path.join(self.app_icon_folder, dst_name)
        image_f.save(dst_path)
        self.extractor_record[(exe_path, group, name)] = True
        return dst_path
    
    def exe_file_icon_extract(self, exe_path:str, save_path:str, UID:str=None)->str|None:
        if self.extractor_record.get(UID, False):
            return None
        img_f = self.extract_exe_icon(exe_path, 0)
        if img_f is None:
            return None
        img_f.save(save_path)
        self.extractor_record[UID] = True
        self.exe_file_icon_d[UID] = save_path
        return save_path

    def get_file_icon(self, request:GV.IconQuery)->str|AIcon:
        host_i = request.host
        path_i = request.path
        if host_i == 'Local' and path_i.endswith('.exe'):
            UID = self.hash_path(host_i, path_i)
            if self.extractor_record.get(UID, False):
                icon_t = self.exe_file_icon_d.get(UID)
                if icon_t:
                    return AIcon(icon_t)
                else:
                    return self.default_app_icon
            save_path = os.path.join(self.exe_file_icon_folder, f"{UID}.png")
            temp_path = self.exe_file_icon_extract(path_i, save_path, UID)

            if temp_path is None:
                return self.default_app_icon
            return AIcon(temp_path)
        ext_name = os.path.splitext(request.name)[1]
        return self.file_icon_d.get(ext_name, self.default_file_icon)
    
    def get_app_icon(self, request:GV.IconQuery)->AIcon:
        exe_path = link2path(request.path)
        if os.path.splitext(exe_path)[1].lower() in ['.exe','dll']:
            path_t = self.app_icon_extract(exe_path, request.group, request.name)
            if not path_t:
                return self.default_app_icon
            return AIcon(path_t)
        else:
            return self.default_app_icon
    
    def get_folder_icon(self, request:GV.IconQuery)->AIcon:
        hash_num = self.hash_path(request.host, request.path)
        icon_t = self.folder_icon_d.get(hash_num, None)
        if isinstance(icon_t, (AIcon,str)):
            return icon_t
        else:
            return self.default_folder_icon
    
    def hash_path(self, host_i:str, path_i:str)->str:
        path_i = host_i + 'path_for_folder_icon_or_exe_file_icon' + path_i
        
        return hash(str(hashlib.md5(path_i.encode()).hexdigest()[:16]))
    
    def hash_app(self, name:str, group:str)->str:
        name_i = name + 'name_for_app_icon' + group
        return hash(str(hashlib.md5(name_i.encode()).hexdigest()[:16]))
    
    def icon_query(self, request:GV.IconQuery)->AIcon:
        match request.type_f:
            case 'file':
                return self.get_file_icon(request)
            case 'app':
                return self.get_app_icon(request.name, request.group)
            case 'folder':
                return self.get_folder_icon(request)
            case _:
                return self.default_file_icon

    def app_icon_save(self, app_name:str, group:str, src_path:str)->str:
        ext_name = os.path.splitext(src_path)[1]
        if ext_name not in ['.png', '.svg', '.ico', 'jpg', 'jpeg', 'bmp']:
            warnings.warn(f"Invalid icon format in app_icon_save: {ext_name}")
            return
        dst_name = f"{group}{self.sign_for_separate}{app_name}"
        dst_path = os.path.join(self.app_icon_folder, dst_name+ext_name)
        path_l = glob.glob(os.path.join(self.app_icon_folder, f"{dst_name}.*"))
        for path_i in path_l:
            os.remove(path_i)
        shutil.copy(src_path, dst_path)
        return dst_path

    def path_icon_save(self, type_f:Literal['file', 'folder', 'exe'], host:str, path:str, src_path:str)->str:   
        if not self.check_format(src_path):
            return
        icon_ext = os.path.splitext(src_path)[1]
        match type_f:
            case 'file':
                save_name = os.path.splitext(path)[1].strip('.')    
                path_l = glob.glob(os.path.join(self.file_icon_folder, f"{save_name}.*"))
                dst_path = os.path.join(self.file_icon_folder, save_name+icon_ext)
                
            case 'folder':
                hash_num = self.hash_path(host, path)
                path_l = glob.glob(os.path.join(self.folder_icons, f"{hash_num}.*"))
                dst_path = os.path.join(self.folder_icons, f"{hash_num}{icon_ext}")
            case 'exe':
                exe_hash = self.hash_path(host, path)
                path_l = glob.glob(os.path.join(self.exe_file_icon_folder, f"{exe_hash}.*"))
                dst_path = os.path.join(self.exe_file_icon_folder, f"{exe_hash}{icon_ext}")
            case _:
                warnings.warn(f"Invalid icon type in path_icon_save: {type_f}")
                return
        for path_i in path_l:
            os.remove(path_i)
        shutil.copy(src_path, dst_path)
        return dst_path

    @Slot()
    def save2xlsx(self):
        app_info_dict = {}
        for info_i in self.app_d.values():
            name_i = info_i.name
            if not name_i:
                continue
            group_i = info_i.group
            chname_i = info_i.chname
            exe_path_i = info_i.exe_path
            dict_t = {'Name':name_i, 'Chinese Name':chname_i, 'EXE Path':exe_path_i}
            app_info_dict.setdefault(group_i, []).append(dict_t)
        with pd.ExcelWriter(self.data_path, mode='w') as writer:
            for name_i, df_i in app_info_dict.items():
                df_t = pd.DataFrame(df_i)
                df_t.to_excel(writer, sheet_name=name_i, index=False)
        print(f'save to {self.data_path}')
    @Slot(GV.IconSaveRequest)
    def IconSaveRequest(self, request:GV.IconSaveRequest):
        type_f = request.type_f
        match type_f:
            case 'app':
                self.app_icon_save(request.name, request.group, request.src, request.path)
            case 'file':
                pass
            case 'folder':
                pass
            case 'exe':
                pass
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
        #self.default_icon = QIcon(self.config.get("default_button_icon", mode="Launcher", widget="shortcut_obj", obj="path"))
        self.default_icon = atuple('Launcher', 'shortcut_obj', 'path', 'default_button_icon')
        self.conduct_l = []
        # self.exe_icon_getter = self.config.get('exe_icon_getter', mode="Launcher", widget='associate_list', obj="path").replace('\\', '/')
    
    def geticon(self, name:str)->Union[str, atuple]:
        path_t = self.icon_dict.get(name, "")
        if path_t:
            return path_t
        else:
            exe_paths = self.df[self.df['Display_Name']==name]['EXE_Path'].values
            if not exe_paths:
                return self.default_icon
            exe_path = exe_paths[0]
            if exe_path.endswith('.exe')and (name not in self.conduct_l):
                target_icon_path = os.path.join(self.icon_dir, name).replace('\\', '/')+'.png'
                if extract_icon(self.exe_icon_getter, exe_path, target_icon_path):
                    self.icon_dict[name] = (target_icon_path).replace('/', '\\')
                    return self.icon_dict[name]
                else:
                    self.icon_dict[name] = self.default_icon
                    return self.default_icon
            else:
                self.icon_dict[name] = self.default_icon
                return self.default_icon
                          
    def save(self):
        self.df.to_excel(self.data_path, index=False)

class SSHManager(QObject):
    con_res=Signal(list)
    def __init__(self, parent:QMainWindow, config:Config_Manager):
        super().__init__()
        self.thread_list = []
        self.config = config.deepcopy()
        self.name = 'PathManager'
        self.config.group_chose(mode='Settings', widget=self.name, obj=None)
        self.server=None
        self.sftp:paramiko.SFTPClient = None
        self.hostname_n = 'Local'
        self.host_type = 'Local'
        self.host = []
        self._load_config()
        self._initMaintainer()
    
    def _load_config(self):
        self.host_config_path = self.config.get("ssh_config")
        if not self.host_config_path:
            self.host_config_path = os.path.expanduser("~/.ssh/config")
        if os.path.exists(self.host_config_path):
            self.remote_hosts = parse_ssh_config(self.host_config_path,
                                        fliter=self.config.get("hostname"))
        else:
            #self.up.tip("Warning", "SSH config file not found, please check the path", {"OK":""}, "")
            self.remote_hosts = {}
        self.wsl_l = self.config.get("wsl")
        self.wsl_d = {i[0]:{'path':i[1], 'user':i[2]} for i in self.wsl_l}
        self.hostd = {'Local':''} | self.wsl_d | self.remote_hosts
        self.hostnames = list(self.hostd.keys())
        self.host_types = {'Local':'Local'} | {i:"WSL" for i in self.wsl_d.keys()} | {i:"Remote" for i in self.remote_hosts.keys()}
        self.connection_timeout = self.config.get("connection_timeout", 10)
        self.filename_flitter = self.config.get("filename_flitter")
    
    def get_config(self, name:str):
        assert name in self.hostd.keys(), f"Invalid host name: {name}"
        type_t = self.host_types[name]
        config_t = self.hostd[name]
        return {'type':type_t, 'config':config_t}

    def _initMaintainer(self):
        return
        self.maintainer = ConnectionMaintainer(self.hostname_n, self.sftp)
        self.maintainer.check_result.connect(self._maintain_result)
        self.maintainer.start()
    
    def change_host(self, host_name:str):
        assert host_name in self.hostd.keys(), f"Invalid host name: {host_name}"
        host_type = self.host_types[host_name]
        self.hostname_n = host_name
        self.host_type = host_type
        if host_type == 'Local':
            self.server = None
            self.sftp = None
            return [True, 'Local', '']
        elif host_type == 'WSL':
            self.server = None
            self.sftp = None
            if not os.path.exists(self.wsl_d[host_name]['path']):
                return [False, 'WSL', 'Path not exists']
            return [True, 'WSL', '']
        self.establish_connection(host_name)
        return ['wait', 'Remote', '']
        
    def establish_connection(self, host_name:str):
        assert host_name in self.remote_hosts.keys(), f"Invalid remote host name: {host_name}"
        host_config = self.remote_hosts[host_name]
        est_thread = ConnectionThread(cre_ssh_con, host_config, host_name, copy.deepcopy(self.connection_timeout))
        est_thread.finished_signal.connect(self._connect_result)
        est_thread.start()
        self.thread_list.append(est_thread)

    @Slot(list)
    def _connect_result(self, result:list):
        if result[0] != self.hostname_n:
            return
        if result[1]:
            self.server, self.sftp = result[2]
            self.con_res.emit([True, ''])
        self.con_res.emit([False, result[2]])
    @Slot(list)
    def _maintain_result(self, result:list):
        hostname, sign_f, error_info = result
        if hostname == self.hostname_n:
            if sign_f:
                self.con_res.emit([True, ''])
            else:
                self.con_res.emit([False, error_info])

class TransferPathManager(SSHManager):
    def __init__(self, parent:QMainWindow, config:Config_Manager):
        super().__init__(parent, config)
        self.path_ptr = atuple('Manager', 'TransferPathManager', 'path')
        UIUpdater.set(self.path_ptr, self._loadPath, type_f='style')
    
    def _loadPath(self, path_d:dict, escape_sign:dict={}):
        self.default_download_path = path_d.get('default_download_path', os.path.abspath('./tmp'))
        self.download_filedialog_root = path_d.get('download_filedialog_root', os.path.abspath('./load'))

    def _filename_fliter(self, name:str)->bool:
        # return True if the file name is allowed else False
        if not self.filename_flitter:
            return True
        for fliter_i in self.filename_flitter:
            if name.startswith(fliter_i):
                return False
        return True
    
    def _wsl_path_preprocess(self, path:str):
        if self.hostname_n not in self.wsl_d.keys():
            return path
        if path.startswith('~'):
            user = self.wsl_d[self.hostname_n]['user']
            path = path.replace('~', f'/home/{user}', 1)
        path = os.path.join(self.wsl_d[self.hostname_n]['path'], path)
        return path
    
    def check(self, path:str) -> Union[None, os.stat_result]:
        if self.host_type == 'WSL':
            path = self._wsl_path_preprocess(path)
        if self.host_type in ['Local', 'WSL']:
            if not os.path.exists(path):
                return None
            return os.stat(path)
        elif self.host_type == 'Remote':
            try:
                # 获取文件状态信息
                return self.sftp.stat(path)
            except FileNotFoundError:
                return None
            except Exception as e:
                warnings.warn(f'Host{self.hostname_n} connection encounters error {e}')
                return None
        else:
            warnings.warn(f"Invalid host type: {self.host_type}")
            return None
    
    def isdir(self, path:str)->bool:
        stat_t = self.check(path)
        if stat_t is None:
            return False
        elif stat.S_ISDIR(stat_t.st_mode):
            return True
    
    def isfile(self, path:str)->bool:
        stat_t = self.check(path)
        if stat_t is None:
            return False
        elif not stat.S_ISDIR(stat_t.st_mode):
            return True
        else:
            return False
        
    def listdir(self, path_f:str)->tuple[list[str],list[os.stat_result]]:
        dir_l = []
        stat_l = []
        if self.host_type == 'WSL':
            path_f = self._wsl_path_preprocess(path_f)
        if self.host_type in ['Local', 'WSL']:
            try:
                if not os.path.exists(path_f):
                    return [], []
                for i in os.listdir(path_f):
                    path_t = os.path.join(path_f, i)
                    stat_t = os.stat(path_t)
                    dir_l.append(i)
                    stat_l.append(stat_t)
                return dir_l, stat_l
            except Exception as e:
                warnings.warn(f'Local file search encounters error {e}')
                return [], []
        elif self.host_type == 'Remote':
            try:
                dir_contents = self.sftp.listdir_attr(path_f)
                return [i.filename for i in dir_contents], dir_contents
                # for entry in dir_contents:
                #     if not self._filename_fliter(entry.filename):
                #         continue
                #     if self._filename_fliter(entry.filename):
                #         dir_l.append(entry.filename)
                #         stat_l.append(entry)
                #     else:
                #         dir_s.append(entry.filename)
                #         stat_s.append(entry)
                # return dir_l+dir_s, stat_l+stat_s
            except FileNotFoundError:
                return [], []
            except Exception as e:
                warnings.warn(f'Host {self.hostname_n} connection encounters error {e}')
                return [], []
        else:
            warnings.warn(f"Invalid host type: {self.host_type}")
            return [], []
    
    def walk(self, src:str):
        return_l = []
        if self.host_type != 'Remote':
            for root, dirs, files in os.walk(src):
                for file_i in files:
                    rel_path = os.path.relpath(root, src)
                    size_i = os.path.getsize(os.path.join(root, file_i))
                    file_path = os.path.join(root, file_i)
                    return_l.append((rel_path, file_i, file_path, size_i))
        else:
            for root, dirs, files in self.sftp_walk(self.sftp, src):
                for file_i in files:
                    rel_path = os.path.relpath(root, src)
                    size_i = self.sftp.stat(os.path.join(root, file_i)).st_size
                    file_path = os.path.join(root, file_i)
                    return_l.append((rel_path, file_i, file_path, size_i))
        return return_l
    
    def sftp_walk(self, sftp, remote_dir):
        try:
            for attr in sftp.listdir_attr(remote_dir):
                remote_path = remote_dir + "/" + attr.filename
                if stat.S_ISDIR(attr.st_mode):
                    yield remote_path, [d.filename for d in sftp.listdir_attr(remote_path) if stat.S_ISDIR(d.st_mode)], [f.filename for f in sftp.listdir_attr(remote_path) if not stat.S_ISDIR(f.st_mode)]
                    yield from self.sftp_walk(sftp, remote_path)
                else:
                    yield remote_path, [], [attr.filename]
        except Exception as e:
            warnings.warn(f'Host {self.hostname_n} connection encounters error {e}')
            return []

class ConnectionThread(QThread):
    finished_signal = Signal(list)
    def __init__(self, function:cre_ssh_con, config:dict, host_name:str, timeout:int=10):
        super().__init__()
        self.function = function
        self.config = config
        self.timeout = timeout
        self.host_name = host_name
    
    def run(self):
        try:
            out = self.function(host_paras=self.config, timeout=self.timeout)
            self.finished_signal.emit([self.host_name, True, out])
        except Exception as e:
            self.finished_signal.emit([self.host_name, False, str(e)])

class ConnectionMaintainer(QThread):
    bar_state = Signal(list)
    stop_signal = Signal(bool)
    server_input = Signal(list)
    def __init__(self, server_name, server:paramiko.SFTPServer, interval:int=10):
        super().__init__()
        self.interval = interval
        self.server_name = server_name
        self.server = server
        self.server_input.connect(self._input_server)
        self.stop_sign = False
    
    @Slot(list)
    def _input_server(self, server:list):
        self.server_name = server[0]
        self.server = server[1]
    
    def stop(self):
        self.stop_sign = True
    
    def run(self):
        while True:
            try:
                server_name = copy.deepcopy(self.server_name)
                if self.server is not None:
                    self.server.stat(".")
                self.check_result.emit([server_name, True, ''])
            except Exception as e:
                self.check_result.emit([server_name, False, str(e)])
            check_interval = 0.1
            for i in range(int(self.interval/check_interval)):
                if self.stop_sign:
                    return
                time.sleep(check_interval)

class TransferMaintainer(QThread):
    bar_state = Signal(list)    # output the state and progress of the transfer
    stop_signal = Signal(bool)  # stop the transfer
    def __init__(self,config:Config_Manager):
        super().__init__()
        self.name = "TransferMaintainer"
        config = config.deepcopy().group_chose(mode='Settings', widget=self.name,obj=None)
        pre = ['Settings', self.name]
        self.l_max = atuple(pre+['local_min_chunck'])
        self.l_min = atuple(pre+['local_max_chunck'])
        self.r_max = atuple(pre+['remote_min_chunck'])
        self.r_min = atuple(pre+['remote_max_chunck'])
        UIUpdater.set(alist(self.l_min, self.l_max, self.r_min, self.r_max), self._loadconfig, alist())
        self.task_queue = []
        self.loop = None  # Event loop for asyncio
        self.state = 'Stop'
    
    def _loadconfig(self, l_min,l_max,r_min,r_max):
        pre = ['Settings', self.name]
        # self.local_min_chunck = config_f.get('local_min_chunck')*1024**2
        self.local_min_chunck = int(l_min*1024**2)
        # self.local_max_chunck = config_f.get('local_max_chunck')*1024**2
        self.local_max_chunck = int(l_max*1024**2)
        #self.remote_min_chunck = config_f.get('remote_min_chunck')*1024**2
        self.remote_min_chunck = int(r_min*1024**2)
        #self.remote_max_chunck = config_f.get('remote_max_chunck')*1024**2
        self.remote_max_chunck = int(r_max*1024**2)

    
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

class TrackThread(QThread):
    output_signal = Signal(dict)
    def __init__(self, file_name:str, monitor_path:str):
        super().__init__()
        self.file_name = file_name
        self.monitor_path = monitor_path

    def run(self):
        try:
            from file_watcher import FileWatcher     # type: ignore
            self.watcher = FileWatcher()
            result_f = self.watcher.start(self.monitor_path, self.file_name, self.output_signal.emit)
            error_f = ''
        except Exception as e:
            result_f = None
            error_f = str(e)
        self.output_signal.emit({'result':result_f, 'error':error_f})

    def close(self):
        self.quit()
        self.wait()
        try:
            self.watcher.stop()
        except Exception:
            pass

class PathTracker:
    def __init__(self):
        pass
    
    def _load_config(self):
        pass

    def create_tag(self):
        name_f = f"__SuperLauncher_Tag.txt"
        path_f = path_join(self.tag_folder, name_f)
        if not os.path.exists(path_f):
            with open(name_f, 'a') as f:
                f.write(f"SuperLauncher_Tag\nFor Path Tracking")
        self.path_f = path_f

    def create_tracker(self):
        drivers = self.get_drives()
        if not drivers:
            return
        if not os.path.exists(self.path_f):
            self.create_tag()
        file_name = os.path.basename(self.path_f)
        for driver in drivers:
            pass
    
    @Slot(str)
    def target_receiver(self, driver:str):
        pass

    def close_tracker(self):
        self.close_timer = QTimer()
        self.close_timer.timeout.connect(self.close_tracker_action)
        self.close_timer.start(self.wait_time)
    
    def close_tracker_action(self):
        for i in self.tracker_list:
            i.close()
    
    def get_drives(self):
        drivers = get_hard_drives()
        if self.monitor_drivers:
            drivers_t = []
            for i in drivers:
                for i_t in self.monitor_drivers:
                    if i.startswith(i_t):
                        drivers_t.append(i)
                        break
            return drivers_t
        else:
            return drivers


