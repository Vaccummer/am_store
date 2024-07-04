import os
import re
import sys
from typing import Literal, Optional, List, Tuple, Dict, Union


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


def pkl(path_f:str, data_f=None):
    # pkl create and read function
    import pickle
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


def txt_read(path_f:str):
    # read txt file and return lines list
    # path_f should point to a document file
    # output is a list of lines(str)
    if not os.path.exists(path_f):
        Warning(f"txt_read function get a illegal path: {path_f}")
        return []
    with open(path_f, 'r', encoding='utf-8') as file_f:
        return [line.strip() for line in file_f.readlines()]
    

def is_path(string_f:str, exsist_check:Literal[True, False]=False):
    # To judge whether a variable is Path or not
    if not isinstance(string_f, str):
        return False
    if not exsist_check:
        return os.path.isabs(string_f)
    else:
        return os.path.exists(string_f)


def excel_to_df(excel_path_f:str, region:str, sheet_name_f:str='Sheet1'):
    # Read XLSX doc and transform it into dataframe
    # region format : 'A1:Z7'
    import pandas as pd
    return pd.read_excel(excel_path_f, sheet_name=sheet_name_f, usecols=region)


def restart_program(path_f):
    # restart python script
    python_f = sys.executable
    os.execl(python_f, python_f, path_f)


def multi(target_f, 
          args_list:Union[List[Tuple], List[Dict]], 
          process_num, 
          pl_stratagey=Literal["queue", "pool"], 
          return_flag:Literal[True, False]=False):
    # parallel processing
    if pl_stratagey == "queue":
        import multiprocessing
        from multiprocessing import Process, Queue
        q_f = Queue()
        q_r = Queue()
        for i_f, arg_f in enumerate(args_list):
            q_f.put([i_f, arg_f])
        process_list = []

        def process_v(q_f:multiprocessing.Queue):
            while not q_f.empty():
                index_f, arg_f = q_f.get()
                if isinstance(arg_f, tuple):
                    target_f(*arg_f)
                elif isinstance(arg_f, dict):
                    target_f(**arg_f)
                else:
                    target_f(arg_f)
        
        def process_r(q_ff:multiprocessing.Queue, q_rr:multiprocessing.Queue):
            while not q_ff.empty():
                index_f, arg_f = q_f.get()
                if isinstance(arg_f, tuple):
                    q_rr.put([index_f, target_f(*arg_f)])
                elif isinstance(arg_f, dict):
                    q_rr.put([index_f, target_f(**arg_f)])
                else:
                    q_rr.put([index_f, target_f(arg_f)])
        
        for i in range(min(process_num, len(args_list))):
            if return_flag:
                process_f = Process(target=process_r, args=(q_f, q_r))
            else:
                process_f = Process(target=process_v, args=(q_f,))
            process_f.start()
            process_list.append(process_f)
        
        for process_f in process_list:
            process_f.join()
        
        if return_flag:
            result_list = []
            while not q_r.empty():
                result_list.append(q_r.get())
            result_list.sort(key=lambda x:x[0])
            return [x[1] for x in result_list]
    else:
        import multiprocessing
        pool_f = multiprocessing.Pool(process_num)
        pool_result_list = []
        for para_i in args_list:
            if isinstance(para_i, tuple):
                async_result = pool_f.apply_async(target_f, args=para_i, callback=print)
            elif isinstance(para_i, dict):
                async_result = pool_f.apply_async(target_f, kwds=para_i, callback=print)
            else:
                async_result = pool_f.apply_async(target_f, args=(para_i,), callback=print)
            pool_result_list.append(async_result)
        pool_f.close()
        pool_f.join()
        return [result_f.get() for result_f in pool_result_list]


def time_count(func_f, args, return_time_flag:Literal[True, False]=False):
    # count the time of a function
    # return the time cost in seconds unit(float number) 
    import time
    start_time = time.time()
    if isinstance(args, tuple):
        output_f = func_f(*args) 
    elif isinstance(args, dict):
        output_f = func_f(**args)
    else:
        output_f = func_f(args)
    end_time = time.time()
    if return_time_flag:
        return [output_f, end_time-start_time]
    else:
        print(f"Time cost: {end_time-start_time:.2f} s")
        return output_f


def get_file_size(path_f:str):
    # get the size of a file or a directory
    size_f = 0
    if os.path.isfile(path_f):
        size_f += os.path.getsize(path_f)
    elif os.path.isdir(path_f):
        for root, dirs, files in os.walk(path_f):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.exists(file_path):
                    size_f += os.path.getsize(file_path)
    return size_f


def get_script_path():
    # get the path of the script
    return os.path.realpath(__file__)


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