import multiprocessing.managers
import os
import re
from typing import Generator, Iterable, Literal, Optional, Union, Any, Callable,Sequence
import warnings
from typing import Union
import multiprocessing
import time 
import pathlib 
from functools import wraps
import pickle
import json
import PIL
import pathlib
## non standard library
import PIL.Image
import pandas
from sympy import sequence
import yaml
from tqdm import tqdm
import numpy
# set terminal print color
from am_store.color_format import *
color_config = TerminalErrorColorConfig()
print_callback = partial(call_back_exception, color_config=process_config(color_config))
sys.excepthook = print_callback

def path_format(string_f:str)->str:
    # turn a string into a formal path of OS
    if not isinstance(string_f, str):
        raise ValueError(f"Input of path_format function should be a string, but get {type(string_f)}")
    else:
        sep = os.sep
        string_f = rf"{string_f}"
        path_t1 = string_f.replace('/', sep)
        path_t2 = path_t1.replace('\\', sep)
        return path_t2

def path_join(*args:tuple[str], mkdir:Literal[True, False]=True)->str:
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

def pkl(path_f:Union[str, pathlib.Path], data_f=None, mkdir:bool=False, force:bool=False)->Any:
    # pkl create and read function
    if data_f is None:
        if os.path.exists(path_f):
            with open(path_f, 'rb') as data_f:
                return pickle.load(data_f)
        else:
            warnings.warn(f'pkl function(read mode) get a illegal path: {path_f}')
            return
    elif path_f and (data_f is not None):
        if not os.path.exists(os.path.dirname(path_f)):
            if mkdir:
                os.makedirs(os.path.dirname(path_f), exist_ok=True)
            else:
                warnings.warn(f"pkl: Superior directory of {path_f} not exists! Pass mkdir=True to create it")
                return
        if os.path.exists(path_f):
            if os.path.isdir(path_f):
                print(f'pkl recive a dir path : "{path_f}" exsists!')
                return
            if force is False:
                print(f'pkl save target path : "{path_f}" exsists!')
                return
            else:
                os.remove(path_f)
        ori_f, ext_f = os.path.splitext(path_f)
        path_f = path_f if ext_f == '.pkl' else ori_f + '.pkl'
        with open(path_f, 'wb') as file_f:
            pickle.dump(data_f, file_f)
        return
    else:
        warnings.warn(f"pkl function get invalid arguments!")
        return

def is_url(str_f:str)->bool:
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

def excel_to_df(excel_path_f:Union[str, pathlib.Path],
                sheet_name_f:Union[str, int, list[str], list[int]]=0, # -1 means all sheets
                region:str=None):
    # region format : 'A1:Z7'
    pandas.ExcelFile()
    return pandas.read_excel(excel_path_f, sheet_name=sheet_name_f, usecols=region)

def multi_single_process(target_f, 
                         arg_queue:multiprocessing.Queue, 
                         task_num:int,
                         count_value, # shared value
                         output_list:list=None,
                         additional_para:Optional[dict]={}):
    # get para, (index, para) format
    while not arg_queue.empty():
        try:
            index_i, para_i = arg_queue.get(timeout=2)
        except Exception:
            return
        if isinstance(para_i, tuple):
            output_i = target_f(*para_i, **additional_para)
        elif isinstance(para_i, dict):
            output_i = target_f(**para_i, **additional_para)
        else:
            output_i = target_f(para_i, **additional_para)
        if output_list:
            output_list.append([index_i, output_i])
        with multiprocessing.Lock():
            count_value.value += 1

def multi_control_process(arg_queue:multiprocessing.Queue,
                           shared_value,
                           bar,):
    while not arg_queue.empty():
        bar.update(shared_value.value-bar.n)
        time.sleep(0.1)
    return

def multi(func_f:Callable, 
          data:Sequence[tuple]|Sequence[dict], 
          process_num:int=None, 
          args:Optional[Sequence[dict]]=None,
          start_method:Literal['fork', 'spawn', 'forkserver']="fork",
          use_torch:Literal[True, False]=False,
          return_need:Literal[True, False]=True,
          tqdm_need:Literal[True, False]=False,
          tqdm_para:dict={})->list|None:
    r"""  parallel processing function
        func_f: function to be conducted

        data: list of arguments, can be list[Tuple] or list[dict], later is recommended

        process_num: number of processes

        args: args origin from the function but apply to certain process, 
        list[dict] format is demanded
        
        start_method: start method of multiprocessing, "fork", "spawn" or "forkserver"
        
        use_torch: whether use torch.multiprocessing or not
        
        return_need: whether return the result or not
        
        tqdm_need: whether show the progress bar or not
        
        tqdm_para: parameters of tqdm, dict format
    """
    assert data, "data is empty"
    assert process_num or args, "process_num and args are both empty"
    if not process_num:
        process_num = len(args)
    else:
        assert len(args) == process_num, "process_num and args are not matched"
    assert process_num < os.cpu_count(), "process_num is too large"

    if use_torch:
        import torch.multiprocessing as mp
    else:
        import multiprocessing as mp
    if os.name == 'nt' and start_method == 'fork':
        warnings.warn("fork start method is not supported on Windows, use spawn instead")
        start_method = 'spawn'
    mp.set_start_method(start_method)
    
    task_num = len(data)
    manager = mp.Manager()
    data_queue = mp.Queue()
    result_list = manager.list() if return_need else None
    count_value = manager.Value('i', 0)

    for i_f, arg_f in enumerate(data):
        data_queue.put([i_f, arg_f])
    process_list = []
    if tqdm_need:
        bar = tqdm(total=task_num, **tqdm_para)
        process_control = mp.Process(target=multi_control_process,
                                args=(data_queue, count_value, bar))
        process_control.start()
    else:
        bar  = None
    
    # process num should be less than the length of work_args_list
    for i in range(process_num, 64):
        process_arg = args[i] if args else {}
        process_f = mp.Process(target=multi_single_process, 
                            args=(func_f, data_queue, task_num, count_value, result_list, process_arg), daemon=False)
        process_f.start()
        process_list.append(process_f)
    
    for process_f in process_list:
        process_f.join()

    if bar != None:
        process_control.join()
        bar.update(task_num-bar.n)
    
    if return_need:
        result_l = list(result_list)
        result_l.sort(key=lambda x:x[0])
        return [x[1] for x in result_list]

def timeit(unit:Literal['h', 'min', 's', 'ms', 'us']='s')->Callable:
    assert unit in ['h', 'min', 's', 'ms', 'us'], f"Invalid time unit: {unit}"
    def iner(func_f:Callable)->Callable:
        @wraps(func_f)  # 保留原函数的元信息
        def wrapper(*args, am_runtag:str='', **kwargs):
            start_time = time.time()  # 记录开始时间
            result = func_f(*args, **kwargs)  # 调用原函数
            end_time = time.time()  # 记录结束时间
            execution_time = end_time - start_time  # 计算执行时间
            cal_dict = {'h': 3600, 'min': 60, 's': 1, 'ms': 1e-3, 'us': 1e-6}  # 计算单位对应的秒数
            execution_time /= cal_dict[unit]
            print(f"timeit loigging! Function: '{func_f.__name__}', Tag: '{am_runtag}', Time: {execution_time:.4f} {unit}")  # 输出函数名和执行时间
            return result  # 返回原函数的结果
        return wrapper  # 返回包装后的函数
    return iner  # 返回包装函数

def lineplot_draw2(
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
    # draw line plot
    from matplotlib import pyplot as plt
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

def save_image_from_matrix(matrix_f:numpy.ndarray, file_path:str|pathlib.Path):
    from PIL import Image
    import cv2
    if not isinstance(matrix, (numpy.ndarray)):
        import torch
        if not isinstance(matrix, (torch.Tensor)):
            import tensorflow as tf
            if not isinstance(matrix, (tf.Tensor)):
                raise ValueError(f"Wrong input type:{matrix.__class__}")
            else:
                matrix = matrix_f.cpu()
        else:
            matrix_f = matrix.detach().cpu().numpy()
    else:
        matrix = matrix_f
    
    if isinstance(matrix, numpy.ndarray):
        # 检查是否是彩色图像（三个通道）
        if matrix.ndim == 3 and matrix.shape[2] in [3, 4]:
            # Pillow支持RGB和RGBA格式
            image = Image.fromarray(matrix.astype(numpy.uint8))
            image.save(file_path)
        elif matrix.ndim == 3 and matrix.shape[2] == 1:
            # 灰度图像
            matrix = numpy.squeeze(matrix, axis=-1)  
            image = Image.fromarray(matrix.astype(numpy.uint8), mode='L')
            image.save(file_path)
        else:
            raise ValueError("Unkown shape of matrix input, process only one matrix once!")
    else:
        raise ValueError(f"nd.array type expected, but receive {type(matrix)}")
    
def tqdm_bar(iter:Iterable, descrition:str, unit:str, length:int)->Iterable:
    pass


class AMImage:
    @staticmethod
    def preprocess_array(array_f):
        if not isinstance(array_f, numpy.ndarray):
            raise ValueError(f"Wrong inumpyut type:{array_f.__class__}")
        array_f = numpy.squeeze(array_f)
        assert array_f.ndim == 2 or (array_f.ndim == 3 and 3 in array_f.shape), f"Wrong array shape: {array_f.shape}"
        if array_f.ndim == 3:
            match array_f.shape:
                case (3, _, _):
                    array_f = numpy.moveaxis(array_f, 0, -1)
                case (_, 3, _):
                    array_f = numpy.moveaxis(array_f, 1, -1)
                case _:
                    pass
        min_val = numpy.min(array_f)
        max_val = numpy.max(array_f)
        if -0.1<min_val <0.1 and 254.9<max_val<255.1:
            return array_f.astype(numpy.uint8)
        else:
            return ((array_f-min_val)/(max_val-min_val)*255).astype(numpy.uint8)

    def __new__(cls, data) -> PIL.Image.Image:
        match data:
            case PIL.Image.Image():
                return data
            case pathlib.Path():
                return PIL.Image.open(data)
            case str():
                return PIL.Image.open(data)
            case numpy.ndarray():
                return PIL.Image.fromarray(cls.preprocess_array(data))
            case torch.Tensor():
                return PIL.Image.fromarray(cls.preprocess_array(data.numpy()))
            case tensorflow.Tensor():
                return PIL.Image.fromarray(cls.preprocess_array(data.numpy()))
            case _:
                raise ValueError(f"Wrong input type:{data.__class__}")
    
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
    
class yml:
    @staticmethod
    def read(yaml_path:str):
        # yaml read function
        if os.path.exists(yaml_path) and (yaml_path.endswith('.yaml') or yaml_path.endswith('.yml')):
            with open(yaml_path, 'r', encoding='utf-8') as data_f:
                return yaml.safe_load(data_f)
        else:
            warnings.warn(f'yml.read function(read mode) get a illegal path: {yaml_path}')
            return
    
    @staticmethod
    def write(yaml_path:str, data_f:dict):
        # yaml create function
        # get both yaml file path and dict input, write dict to path provided

        if yaml_path.endswith('.yaml') or yaml_path.endswith('.yml'):
            with open(yaml_path, 'w', encoding='utf-8') as file_f:
                yaml.dump(data_f, file_f, default_flow_style=False, sort_keys=False)
            return
        else:
            warnings.warn(f'yml.write function detected no valid path')
    
    @staticmethod
    def edit(yaml_path:str, edit_info:dict, force=False):
        '''
        # yaml edit function
        # get both yaml file path and dict input, edit data of path provided
        # edit_info can be common dict or flatten dict(keys stored in tuple)
        # if force is True, the function will create keys that not exist in the yaml file
        # Warning: this function will overwrite the original yaml file'''
        yaml_data = yml.read(yaml_path)
        if not yaml_data:
            return
        dict_n = dicta.edit(yaml_data, edit_info, force)
        yml.write(yaml_path, dict_n)

    @staticmethod
    def format(dict_or_yaml_path:Union[str, dict]):
        if isinstance(dict_or_yaml_path, dict):
            return yaml.dump(dict_or_yaml_path, default_flow_style=False, sort_keys=False)
        elif isinstance(dict_or_yaml_path, str):
            dict_f = yml.read(dict_or_yaml_path)
            if not dict_f:
                return
            else:
                return yaml.dump(dict_f)

class AMPATH(pathlib.Path):
    _flavour = pathlib.Path()._flavour  
    _ext_map = {
        "yaml": [".yml", ".yaml"],
        "json": [".json"],
        "pickle": [".pkl"],
        "torch": [".pth", ".pt"],
        "numpy": [".npy"],
        "text": [".txt", ".log"],
        "csv": [".csv"],
        "excel": [".xlsx", ".xls"],
        "jpg": [".jpg", ".jpeg", ".png"],
        "video": [".mp4", ".avi"],
    }
    direct_map = {value_i:key for key, values in _ext_map.items() for value_i in values}
    def __new__(cls, *args, mkdir:bool=False, abs:bool=False, **kwargs):
        # 调用父类的__new__方法，确保正确初始化_pathlib.Path
        self = super().__new__(cls, *args, **kwargs)
        if abs:
            self = self.resolve()
        if mkdir:
            if not self.exists():
                self.mkdir(parents=True, exist_ok=True)
        return self
    
    def __add__(self, other:str):
        if not isinstance(other, str):
            raise TypeError(f"Can only concatenate str to AMPATH, but get {type(other)}")
        return self.joinpath(other)
    
    def _get_func(self, ext_name:str):
        func_name = self.direct_map.get(ext_name, None)
        if func_name is None:
            warnings.warn(f"Amread can not recognize {ext_name} , use text read as default!")
            return self._text
        else:
            try :
                return getattr(self, f"_{func_name}")
            except Exception as e:
                raise NotImplementedError(f"{func_name} not implemented yet! ")
    
    def amget(self, attribute_name:str):
        try:
            return getattr(self, attribute_name)
        except Exception as e:
            return None
    
    def amread(self, read_func:str=None, **kwargs):
        if not self.exists():
            raise FileNotFoundError(f"File not found: {self}")
        if not self.is_file():
            raise IsADirectoryError(f"Path is a directory: {self}")
        if read_func is None:
            ext_name = self.suffix
            func = self._get_func(ext_name)
        else:
            func = self.amget(f"_{read_func}")
            if func is None:
                raise NotImplementedError(f"{read_func} not implemented yet, print '._ext_map' to check available functions")
        return func(**kwargs)
    
    def amsave(self, data_f, mkdr:bool=True, func_f:str=None, **kwargs):
        if not self.parent.exists():
            if mkdr:
                self.parent.mkdir(parents=True, exist_ok=True)
            else:
                raise FileNotFoundError(f"File not found: {self}")
        if func_f is None:
            ext_name = self.suffix
            func = self._get_func(ext_name)
        else:
            func = self.amget(f"_{func_f}")
            if func is None:
                raise NotImplementedError(f"{func_f} not implemented yet, print '._ext_map' to check available functions")
        return func(data_f=data_f, **kwargs)
    
    def amsize(self, unit:Literal['B', 'KB', 'MB', 'GB', "T"]='MB')->float:
        divide_dict = {'B':1, 'KB':1024, 'MB':1024**2, 'GB':1024**3, "TB":1024**4}
        assert unit in divide_dict.keys(), f"Invalid unit: {unit}"
        if not  self.exists():
            raise FileNotFoundError(f"File not found: {self}")
        size_f = 0
        if self.is_file():
            size_f = self.stat().st_size
            return size_f/divide_dict[unit]
        else:
            for item in self.rglob('*'):  # 使用 rglob 遍历所有文件和子目录
                if item.is_file():  # 只计算文件大小
                    total_size += item.stat().st_size
        return size_f/divide_dict[unit]
    
    def mkdir(self, parents:bool=True, exist_ok:bool=True)->'AMPATH':
        super().mkdir(parents=parents, exist_ok=exist_ok)
        return self

    def amremove(self, recursive:bool=False)->None:
        import shutil
        if not self.exists():
            print(f"Path not found: {self}, skip remove")
        if self.is_file():
            self.unlink()
        elif self.is_dir():
            if recursive:
                shutil.rmtree(self)
            else:
                if self.is_empty():
                    self.rmdir()
                else:
                    warnings.warn(f"Directory not empty: {self}, use recursive=True to remove all files")
    
    def amrename(self, new_name:str)->None:
        new_path = self.parent.joinpath(new_name)
        self.rename(new_path)

    def _yaml(self, data_f:dict=None, **kwargs)->dict:
        if data_f is None:
            return yml.read(str(self), **kwargs)
        else:
            yml.write(str(self), data_f, **kwargs)
    
    def _json(self, data_f:dict=None, **kwargs)->dict:
        if data_f is None:
            with open(str(self), 'r') as file:
                data = json.load(file, **kwargs)
            return data
        else:
            with open(str(self), 'w') as file:
                json.dump(data_f, file, **kwargs)
    
    def _pickle(self, data_f=None, **kwargs)->Any:
        if data_f is None:
            return pkl(str(self), **kwargs)
        else:
            pkl(str(self), data_f, **kwargs)
    
    def _text(self, data_f:str=None, **kwargs)->list[str]:
        if data_f is None:
            with open(str(self), 'r', **kwargs) as file:
                data = file.readlines()
                data = [line.strip() for line in data]
            return data
        else:
            with open(str(self), 'w', **kwargs) as file:
                file.write(data_f)
    
    def _csv(self, data_f:pandas.DataFrame=None, **kwargs)->pandas.DataFrame:
        if data_f is None:
            return pandas.read_csv(str(self), **kwargs)
        else:
            data_f.to_csv(str(self), **kwargs)
    
    def _excel(self, data_f:pandas.DataFrame=None, **kwargs)->pandas.DataFrame:
        import pandas as pd
        if data_f is None:
            return pd.read_excel(str(self), **kwargs)
        else:
            data_f.to_excel(str(self), **kwargs)
    
    def _jpg(self, data_f:PIL.Image.Image=None, **kwargs)->PIL.Image.Image:
        if data_f is None:
            return PIL.Image.open(str(self), **kwargs)
        else:
            data_f.save(str(self), **kwargs)
    
    def _torch(self, data_f, **kwargs):
        import torch
        if data_f == None:
            return torch.load(self, **kwargs)
        else:
            torch.save(data_f, self, **kwargs)
    
    def _numpy(self, data_f, **kwargs):
        import numpy as np
        if data_f == None:
            return np.load(self, **kwargs)
        else:
            np.save(self, data_f, **kwargs)

    def _video(self, data_f:list[numpy.ndarray]=None, ignore_check:bool=True,**kwargs)->Union[list[numpy.ndarray], None]:
        try:
            import imageio
        except Exception as e:
            warnings.warn('Please install imageio first! Use command: pip install imageio[ffmpeg]')
            return
        if data_f is None:
            reader = imageio.get_reader(str(self))
            frames = [frame for frame in reader]
            return frames
        else:
            assert all(isinstance(frame, numpy.ndarray) for frame in data_f), "Wrong input type, please use iteration of numpy.ndarray"
            try:
                writer = imageio.get_writer(str(self), **kwargs)
                for frame in data_f:
                    if not ignore_check:
                        if frame.min() < 0 or frame.max() > 255:
                            frame = (frame - frame.min()) / (frame.max() - frame.min()) * 255
                    writer.append_data(frame)
                writer.close()
            except Exception as e:
                warnings.warn(f"Error in writing video:{str(self)}, encounter error: {e}")

