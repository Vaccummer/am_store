from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import *
from Scripts.tools.toolbox import *
import numpy as np
from Scripts.ui.custom_widget import AIcon
from Scripts.manager.config_ui import Config_Manager  
from Scripts.manager.config_ui import UIUpdater
# from Scripts.manager.ui import *


class LauncherPathManager(object):
    def __init__(self, config:Config_Manager):
        self.config = config
        self.data_path = AMPATH(self.config[atuple('Launcher', 'settings_xlsx_path')])
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
        #self.default_app_icon_path = self.config.get('default_app_icon', mode="Launcher", widget='associate_list', obj="path")
        self.default_app_icon_path = atuple('Launcher', 'associate_list', 'path','default_app_icon')
        self.default_app_icon = self.default_app_icon_path
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
    
    def get_app_icon(self, name, group=None)->Union[str, atuple]:
        if group:
            icon_path = self.app_icon_d[group].get(name, "")
        else:
            icon_path, group = self._find_icon_in_all_groups(name)
        if icon_path:
            return icon_path
        if not group:
            return self.default_app_icon

        exe_entry = self.df[group][self.df[group]['Name'] == name]
        if exe_entry.empty:
            return self.default_app_icon

        exe_path = exe_entry.iloc[0]['EXE Path']
        icon_key = f"{group}{self.sign_for_separate}{name}"
        target_icon_path = os.path.join(self.app_icon_folder, icon_key).replace('\\', '/')+'.png'

        if exe_path.endswith('.exe') and name not in self.conduct_l:
            self.conduct_l.append(name)
            if extract_icon(self.exe_icon_getter, exe_path, target_icon_path):
                self.app_icon_d[group][name] = target_icon_path
                return AIcon(self.app_icon_d[group][name])
            else:
                self.app_icon_d[group][name] = self.default_app_icon_path

        return self.default_app_icon

    def get_icon(self, name, group=None)->Union[str, atuple]:
        return self.get_app_icon(name, group)
    
    def _find_icon_in_all_groups(self, name):
        for group, app_dict in self.app_icon_d.items():
            icon_path = app_dict.get(name, "")
            if icon_path:
                return icon_path, group
        return "", None

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
        self.exe_icon_getter = self.config.get('exe_icon_getter', mode="Launcher", widget='associate_list', obj="path").replace('\\', '/')
    
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
        self.up = parent
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
            self.up.tip("Warning", "SSH config file not found, please check the path", {"OK":""}, "")
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

class PathManager(SSHManager):
    def __init__(self, parent:QMainWindow, config:Config_Manager):
        super().__init__(parent, config)

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
        
    def listdir(self, path_f:str)->List[list]:
        dir_l = []
        stat_l = []
        dir_s = []
        stat_s = []
        if self.host_type == 'WSL':
            path_f = self._wsl_path_preprocess(path_f)
        if self.host_type in ['Local', 'WSL']:
            try:
                if not os.path.exists(path_f):
                    return [], []
                for i in os.listdir(path_f):
                    path_t = os.path.join(path_f, i)
                    stat_t = os.stat(path_t)
                    if self._filename_fliter(i):
                        dir_l.append(i)
                        stat_l.append(stat_t)
                    else:
                        dir_s.append(i)
                        stat_s.append(stat_t)
                return dir_l+dir_s, stat_l+stat_s
            except Exception as e:
                warnings.warn(f'Local file search encounters error {e}')
                return [], []
        elif self.host_type == 'Remote':
            try:
                dir_contents = self.sftp.listdir_attr(path_f)
                for entry in dir_contents:
                    if not self._filename_fliter(entry.filename):
                        continue
                    if self._filename_fliter(entry.filename):
                        dir_l.append(entry.filename)
                        stat_l.append(entry)
                    else:
                        dir_s.append(entry.filename)
                        stat_s.append(entry)
                return dir_l+dir_s, stat_l+stat_s
            except FileNotFoundError:
                return [], []
            except Exception as e:
                warnings.warn(f'Host {self.hostname_n} connection encounters error {e}')
                return [], []
        else:
            warnings.warn(f"Invalid host type: {self.host_type}")
    
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
    server_input = Signal(list)
    check_result = Signal(list)
    def __init__(self, server_name, server:paramiko.SFTPServer, interval:int=10):
        super().__init__()
        self.interval = interval
        self.server_name = server_name
        self.server = server
        self.server_input.connect(self._input_server)
        self.stop_sign = False
    
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
        UIUpdater.set(alist(self.l_min, self.l_max, self.r_min, self.r_max), self._loadconfig, 
                      alist())
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

