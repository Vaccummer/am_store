import os
from typing import Literal, Union, Any, Sequence
import warnings
from typing import Union
import pathlib 
import json
import PIL
import pathlib
## non standard library
import PIL.Image
import pandas
import yaml
import numpy

# tool class
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
    @staticmethod
    def join(*args:Sequence[str], mkdir:bool=True)->str:
        return path_join(*args, mkdir=mkdir)

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
