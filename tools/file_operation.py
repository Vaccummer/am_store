from copy import deepcopy
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


# if __name__ == '__main__':
#     # for i in find(r'D:\Document\Desktop\amz\lib\**'):
#     #     print(i)
#     pass
