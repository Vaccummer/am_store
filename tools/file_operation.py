from copy import deepcopy
import shutil
import sys
import stat
import os
from typing import Literal
from pathlib import Path
from dataclasses import dataclass
import re
from am_store.Logger.logger import get_logger

platform = sys.platform
logger =  get_logger()
exchange1 = "1exchangefindfunction"
exchange2 = "2exchangefindfunction"
exchange3 = "3exchangefindfunction"
exchange4 = "4exchangefindfunction"
exchange5 = "5exchangefindfunction"

color_list = [f"\033[{i}m" for i in range(37, 30, -1)]
FILE_STORE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'file_store')
FILE_DICT = {}

def _init_file_store():
    if not os.path.exists(FILE_STORE):
        os.makedirs(FILE_STORE, exist_ok=True)
        return
    for file in os.listdir(FILE_STORE):
        ext_name = os.path.splitext(file)[1]
        FILE_DICT[ext_name] = os.path.join(FILE_STORE, file)

_init_file_store()

@dataclass
class PathInFo:
    path:str
    mode:Literal['file','directory','link']
    st_result:os.stat_result
    size:int
    time_create:int
    time_modify:int
    time_access:int
    def __init__(self, path:str|Path):
        self.path = str(path)
        stat_f = path.stat()
        if stat.S_ISDIR(stat_f.st_mode):
            self.mode = 'directory'
        elif stat.S_ISLNK(stat_f.st_mode):
            self.mode = 'link'
        else:
            self.mode = 'file'
        self.st_result = stat_f
        self.size = stat_f.st_size
        self.time_create = stat_f.st_ctime
        self.time_modify = stat_f.st_mtime
        self.time_access = stat_f.st_atime

@dataclass
class PreprocessResult:
    def __init__(self, path:Path, format:Literal['relative','user', 'absolute'], root:str, recursive:bool):
        self.path:Path = path
        self.format:Literal['relative','user', 'absolute'] = format
        self.root:str = root
        self.recursive:bool = recursive

class TreeNode:
    def __init__(self, value:PathInFo|str):
        self.value = value  
        self.children = []  

    def add(self, child):
        self.children.append(child)

    def __str__(self)->str:
        return str(self.value)
    
def str_tree(tree:TreeNode, str_l:list[str]|None=None, depth:int=0)->list[str]:
    if str_l is None:
        str_l = []
    str_l.append('-' * depth + f"{color_list[depth]}{str(tree)}\033[0m"+'\n')
    for child in tree.children:
        str_tree(child, str_l, depth+1)
    return ''.join(str_l)

def preprocess(pattern:str)->PreprocessResult:
    if pattern.startswith('~'):
        pattern = os.path.expanduser(pattern)
        return PreprocessResult(Path(pattern), 'user', os.path.expanduser('~'), recursive)
    path_f = Path(pattern)
    parts_ori = path_f.parts
    parts_n = []
    if "**" in parts_ori:
        recursive = True
        for p in parts_ori:
            if p == "**" and parts_n and parts_n[-1] == "**":
                continue
            parts_n.append(p)
        path_f = Path(*parts_n)
    else:
        recursive = False
    if path_f.is_absolute():
        return PreprocessResult(path_f, 'absolute', '', recursive)
    else:

        path_f = path_f.absolute()
        return PreprocessResult(path_f, 'relative', os.getcwd(), recursive)

def _to_result(path:Path, stat_need:bool)->str|PathInFo:
    if stat_need:
        return PathInFo(path)
    else:
        return str(path)

def _match(string:str, pattern:str, use_regex:bool)->bool:
    if not use_regex:
        pattern_f = pattern.replace('*', exchange1)
        pattern_f = re.escape(pattern_f)
        pattern_f = pattern_f.replace(exchange1, '.*')
        pattern_f = f"^{pattern_f}$"
        return re.match(pattern_f, string) is not None
    else:
        pattern_f = pattern.replace('*', exchange1)
        pattern_f = pattern_f.replace('<', exchange2)
        pattern_f = pattern_f.replace('>', exchange3)
        pattern_f = pattern_f.replace('?', exchange4)
        pattern_f = pattern_f.replace('+', exchange5)
        
        pattern_f = re.escape(pattern_f)
        pattern_f = pattern_f.replace(exchange1, '.*')
        pattern_f = pattern_f.replace(exchange2, '[')
        pattern_f = pattern_f.replace(exchange3, ']')
        pattern_f = pattern_f.replace(exchange4, '?')
        pattern_f = pattern_f.replace(exchange5, '+')
        pattern_f = f"^{pattern_f}$"
        return bool(re.match(pattern_f, string))

def _match_path(path:Path, pattern:str, mode:Literal['a','f','d'],
                remain_patterns:list[str], use_regex:bool, total_match_result:list[str], silence:bool=False):
    if remain_patterns:
        if not path.is_dir():
            return
        for p in path.iterdir():
            if pattern == "**":
                if _match(p.name, remain_patterns[0], use_regex):
                    if p.is_dir():
                        _match_path(p, remain_patterns[0], mode, remain_patterns[1:], use_regex, total_match_result, silence)
                    else:
                        total_match_result.append(p)
                elif p.is_dir():
                    _match_path(p, "**", mode, remain_patterns, use_regex, total_match_result, silence)
                continue
            elif _match(p.name, pattern, use_regex) and p.is_dir():
                _match_path(p, remain_patterns[0], mode, remain_patterns[1:], use_regex, total_match_result, silence)
    else:
        if pattern == "**":
            if not silence:
                logger.warning(title='Performance Warning', message='Using ** in last position is not recommended, it may cause performance issues')
            for path_i in path.rglob('*'):
                total_match_result.append(path_i)
        else:
            for p in path.iterdir():
                if not _match(p.name, pattern, use_regex):
                    continue
                match mode:
                    case "a":
                        total_match_result.append(p)
                    case "f" | p.is_file():
                        total_match_result.append(p)
                    case "d" | p.is_dir():
                        total_match_result.append(p)

def find(pattern:str, mode:Literal['a','f','d']='a', stat_need:bool=False, use_regex:bool=False, silence:bool=False)->list[str]|list[PathInFo]:
    """
    pattern: str, string to match the path
        +: match one or more certain character
        *: match zero or more any character
        **: recursive match
        ?: match one character or none
        <>: match any one character in the range
        """
    total_match_result = []
    info = preprocess(pattern)
    if info.path.exists() and not use_regex:
        return [_to_result(info.path, stat_need)]
    path_t = deepcopy(info.path)   
    if info.format != "absolute":
        path_t = path_t.relative_to(Path(info.root))
    path_parts = list(path_t.parts)
    if info.format == "absolute":
        start_path = Path(path_parts.pop(0))
    else:
        start_path = Path(info.root)
    _match_path(start_path, path_parts[0], mode, path_parts[1:], use_regex, total_match_result, silence)
    return [_to_result(r, stat_need) for r in total_match_result]

def delete_cb(func, path_f, exc_info):
    try:
        os.chmod(path_f, stat.S_IWRITE)
        func(path_f)
        return True
    except Exception as e:
        logger.error(title='DeleteError', message=f'{type(e).__name__} when "{path_f}"->"/null", {e}')

def _rm(path_f:str|Path)->None:
    if os.path.isdir(path_f):
        shutil.rmtree(path_f, onerror=delete_cb)
    else:
        try:
            os.remove(path_f)
        except PermissionError:
            os.chmod(path_f, stat.S_IWRITE)
            os.remove(path_f)

def rm(path:str|Path, recursive:bool=False, use_regex:bool=False):
    path_l = find(path, use_regex=use_regex)
    for path_i in path_l:
        if os.path.isdir(path) and not recursive:
            continue
        try:
            _rm(path_i)
        except Exception as e:
            logger.error(message=f'"{path}"->/null', exc=e)
    
def mv(path:str|Path, new_path:str|Path, force:bool=False):
    if os.path.exists(new_path):
        if not force:
            logger.warning(title='FileExists', message=f'Dst already exists: "{new_path}"')
            return
        else:
            rm(new_path, recursive=True)
    shutil.move(path, new_path)

def size(path:str|Path)->int:
    if not os.path.exists(path):
        logger.warning(title='DirectoryInvalid', message=f'File or directory not found: "{path}"')
    if os.path.isdir(path):
        size_total = 0
        for root, dirs, files in os.walk(path):
            for file in files:
                size_total += os.path.getsize(os.path.join(root, file))
        return size_total
    else:
        return os.path.getsize(path)

def new(path:str|Path, mkdir:bool=False)->bool:
    path_f = os.path.abspath(path)
    dir_path = os.path.dirname(path_f)
    if not os.path.exists(dir_path):
        if mkdir:
            os.makedirs(dir_path, exist_ok=True)
        else:
            raise FileNotFoundError(f'Upper directory not found: "{dir_path}", use mkdir=True to create it')
    ext_name = os.path.splitext(path_f)[1]
    if not ext_name:
        os.makedirs(path_f, exist_ok=True)
        return True
    else:
        ori_path = FILE_DICT.get(ext_name, None)
        if ori_path:
            shutil.copy(ori_path, path_f)
            return True
        else:
            logger.warning(title='FileNotFound', message=f"File Store don't have this file: {ext_name}")
            return False

def _tree(path:Path, depth:int, spec:bool, result_out:TreeNode)->None:
    depth = max(depth, 0)
    if depth == 0:
        return
    if not path.is_dir():
        if spec:
            node_i = TreeNode(PathInFo(path))
            result_out.add(node_i)
        else:
            node_i = TreeNode(str(path.name))
            result_out.add(node_i)
    for p in path.iterdir():
        if spec:
            node_i = TreeNode(PathInFo(p))
        else:
            node_i = TreeNode(str(p.name))
        if p.is_dir():
            result_out.add(node_i)
            _tree(p, depth-1, spec, node_i)
        else:
            result_out.add(node_i)

def tree(path:str|Path, depth:int=1, spec:bool=False)->TreeNode:
    '''
    path: str, path to the directory
    depth: int, depth of the tree
    spec: bool, if true, data will be in PathInFo
    '''
    depth = max(depth, 1)
    if not (os.path.exists(path) and os.path.isdir(path)):
        logger.warning(title='DirectoryInvalid', message=f'Path is not a valid directory: "{path}"')
        return {}
    path_f = Path(path)
    if spec:
        result_out = TreeNode(PathInFo(path_f))
    else:
        result_out = TreeNode(str(path_f))
    _tree(path_f, depth, spec, result_out)
    return result_out



if __name__ == '__main__':
    a = Path('D:/Document/Desktop/amz/lib/')
    print(str_tree(tree(r'D:\Document\Desktop\amz', spec=False, depth=4)))
