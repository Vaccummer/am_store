import os
import re
import sys
from typing import Literal, Optional, List, Tuple, Dict, Union
import warnings
from typing import Union

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
    
class yml:
    @staticmethod
    def read(yaml_path:str):
        # yaml read function
        import yaml
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
        import yaml
        if yaml_path.endswith('.yaml') or yaml_path.endswith('.yml'):
            with open(yaml_path, 'w', encoding='utf-8') as file_f:
                yaml.dump(data_f, file_f, default_flow_style=False, sort_keys=False)
            return
        else:
            warnings.warn(f'yml.write function detected no valid path')
    
    @staticmethod
    def edit(yaml_path:str, edit_info:dict, force=False):
        # yaml edit function
        # get both yaml file path and dict input, edit data of path provided
        # edit_info can be common dict or flatten dict(keys stored in tuple)
        # if force is True, the function will create keys that not exist in the yaml file
        # Warning: this function will overwrite the original yaml file
        yaml_data = yml.read(yaml_path)
        if not yaml_data:
            return
        dict_n = dicta.edit(yaml_data, edit_info, force)
        yml.write(yaml_path, dict_n)

    @staticmethod
    def print(dict_or_yaml_path:Union[str, dict]):
        import yaml
        if isinstance(dict_or_yaml_path, dict):
            print(yaml.dump(dict_or_yaml_path, default_flow_style=False, sort_keys=False))
        elif isinstance(dict_or_yaml_path, str):
            dict_f = yml.read(dict_or_yaml_path)
            if not dict_f:
                return
            else:
                print(yaml.dump(dict_f))


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
          work_args_list:Union[List[Tuple], List[Dict]], 
          process_num, 
          process_args_list:Optional[List[Dict]]=None,
          pl_stratagey:Literal["queue", "pool"]="pool", 
          return_flag:Literal[True, False]=False):
    # parallel processing
    if pl_stratagey == "queue":
        import multiprocessing
        from multiprocessing import Process, Queue
        q_f = Queue()
        q_r = Queue()
        for i_f, arg_f in enumerate(work_args_list):
            q_f.put([i_f, arg_f])
        process_list = []

        def process_v(target_f, q_f:multiprocessing.Queue):
            while not q_f.empty():
                index_f, arg_f = q_f.get()
                if isinstance(arg_f, tuple):
                    target_f(*arg_f)
                elif isinstance(arg_f, dict):
                    target_f(**arg_f)
                else:
                    target_f(arg_f)
        
        def process_r(target_f, q_ff:multiprocessing.Queue, q_rr:multiprocessing.Queue, additional_para={}, ):
            while not q_ff.empty():
                index_f, arg_f = q_f.get()
                if isinstance(arg_f, tuple):
                    q_rr.put([index_f, target_f(*arg_f, **additional_para)])
                elif isinstance(arg_f, dict):
                    q_rr.put([index_f, target_f(**arg_f, **additional_para)])
                else:
                    q_rr.put([index_f, target_f(arg_f, **additional_para)])

        from functools import partial

        for i in range(min(process_num, len(work_args_list))):
            if process_args_list:
                if return_flag:
                    process_f = Process(target=process_r, args=(target_f, q_f, q_r, process_args_list[i]))
                else:
                    process_f = Process(target=process_v, args=(target_f, q_f, process_args_list[i]))
            else:
                if return_flag:
                    process_f = Process(target=process_r, args=(target_f, q_f, q_r))
                else:
                    process_f = Process(target=process_v, args=(target_f, q_f,))
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
        for para_i in work_args_list:
            if isinstance(para_i, tuple):
                async_result = pool_f.apply_async(target_f, args=para_i)
            elif isinstance(para_i, dict):
                async_result = pool_f.apply_async(target_f, kwds=para_i)
            else:
                async_result = pool_f.apply_async(target_f, args=(para_i,))
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


def get_file_size(path_f:str, unit:Literal['B', 'KB', 'MB', 'GB']='MB'):
    # get the size of a file or a directory
    size_f = 0
    if os.path.isfile(path_f):
        size_f += os.path.getsize(path_f)
    elif os.path.isdir(path_f):
        for root, dirs, files in os.walk(path_f):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    size_fi = os.path.getsize(file_path)
                except Exception:
                    size_fi = 0
                size_f += size_fi
    divide_dict = {'B':1, 'KB':1024, 'MB':1024**2, 'GB':1024**3, "TB":1024**4}
    return size_f/divide_dict[unit]


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