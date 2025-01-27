from typing import Literal, Union, Callable, Any, Optional

MODE:str = "Launcher"
HOST:str = 'Local'
HOST_TYPE:str = "Local"
CONNECT:bool = True
CON_ERROR:str = ''
CLOSE_ACTION:list[callable] = []
GEOMETRY:list[int] = [0, 0, 0, 0]

UpdateSign = Literal[None, 'size', 'font', 'icon', 'config', 'height', 'margin', 'unpack', 'style']
class LaunchTask:
    __slots__ = ['name', 'path', 'type', 'host']
    def __init__(self, name:str='', path:str='', type_f:Literal['file', 'dir']='', host:str=''):
        self.name = name
        self.path = path
        self.type = type_f
        self.host = host

class FileOperation:
    __slots__ = ['operation', 'src', 'dst', 'src_host', 'dst_host']
    def __init__(self,operation:Literal['delete', 'copy', 'move','create']='', 
                 src:list|str='', dst:str='', src_host:str='', dst_host:str=''):
        self.operation = operation
        self.src = src
        self.dst = dst
        self.src_host = src_host
        self.dst_host = dst_host

class FileProcessProgressInfo:
    __slots__ = ['ID', 'filename', 'progress']
    def __init__(self, ID:str, filename:str, progress:float):
        self.ID = ID
        self.filename = filename
        self.progress = progress

class TransferInfo:
    __slots__ = ['ID', 'src', 'dst', 'src_host', 'dst_host', 'size', 'type_f']
    def __init__(self, ID:str, src:str, dst:str, src_host:str, dst_host:str, size:int, type_f:Literal['file', 'dir']):
        self.ID = ID
        self.src = src
        self.dst = dst
        self.src_host = src_host
        self.dst_host = dst_host
        self.size = size
        self.type_f = type_f

class IconQuery:
    __slots__ = ['type_f', 'name', 'chname', 'group', 'path', 'host']
    def __init__(self, type_f:Literal['file', 'app', "folder"], name:str, chname:str='', group:str=None, path:str='', host:str=''):
        self.type_f = type_f
        self.name = name
        self.chname = chname
        self.group = group
        self.path = path
        self.host = host

class IconSaveRequest:
    __slots__ = ['type_f', 'name', 'chname', 'group', 'path','host', 'icon_path']
    def __init__(self, type_f:Literal['file', 'app', "folder", 'exe'], icon_path:str, path:str=None, host:str=None, name:str=None, group:str=None, chname:str=None):
        self.type_f = type_f
        self.name = name
        self.chname = chname
        self.group = group   
        self.path = path
        self.host = host
        self.icon_path = icon_path

class LauncherAppInfo:
    __slots__ = ['ID','name', 'chname', 'group', 'exe_path', 'icon_path']
    def __init__(self, ID:int, name:str, chname:str, group:str, exe_path:str, icon_path:str=''):
        self.ID = ID
        self.name = name
        self.chname = chname
        self.group = group
        self.exe_path = exe_path
        self.icon_path = icon_path

    def deepcopy(self):
        return LauncherAppInfo(self.ID, self.name, self.chname, self.group, self.exe_path)

class IconSaveRequest:
    __slots__ = ['type_f', 'name', 'group', 'path', 'host', 'src']
    def __init__(self, type_f:Literal['app', 'file', 'folder', 'exe'], name:str, group:str, path:str, host:str, src:str):
        self.type_f = type_f
        self.name = name
        self.group = group
        self.path = path
        self.host = host
        self.src = src
