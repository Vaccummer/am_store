import multiprocessing.managers
import os
import re
from typing import Iterable, Literal, Optional, Union, Any, Callable,Sequence
import warnings
from typing import Union
import multiprocessing
import time 
import pathlib 
from functools import wraps
import pickle
import pathlib
## non standard library
import pandas
from tqdm import tqdm
import numpy

# tool function
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
