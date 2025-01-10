from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import *
from ..tools.toolbox import *
import numpy as np

class Asize(QSize):
    def __init__(self, width:int, height:int):
        super().__init__(width, height)
    def __mul__(self, c:Union[int, float]):
        return QSize(int(self.width()*c), int(self.height()*c))
    def q(self):
        return QSize(self.width(), self.height())

class AIcon(QIcon):
    def __init__(self, file_path):
        if isinstance(file_path, atuple):
            self.file_path = UIUpdater.config.get(file_path,'')
            super().__init__(self.file_path)
        elif isinstance(file_path, str):
            self.file_path = file_path
            super().__init__(file_path)
        elif isinstance(file_path, QIcon):
            super().__init__(file_path)
        else:
            super().__init__()
        
    def get_file_path(self):
        return self.file_path
    def q(self):
        QIcon(self.file_path)

class Config_Manager(object):
    @classmethod
    def set_config_path(cls,yaml_path:str):
        if not hasattr(cls, 'config'):
            config = yml.read(yaml_path)
            cls.config = dicta.flatten_dict(config)
            cls.yaml_path = yaml_path
            config_0 = cls._calSize(cls.config)
            config_1 = dicta.unflatten_dict(config_0)
            cls.config = adict(config_1)
            a = 1
    def __init__(self, 
                 wkdir:str,
                 mode_name:str=None, 
                 widget_name:str=None, 
                 obj_name:str=None,
                 copy:bool=False):
        self.wkdr = wkdir
        self.mode = mode_name
        self.widget = widget_name
        self.obj = obj_name
        self.pre = []
    
    def deepcopy(self):
        new_copy = Config_Manager(self.wkdr, None, None, None, True)
        return new_copy
    @staticmethod
    def _calSize(config:dict):
        scr_x, scr_y = get_screen_size('pixel')
        res_x = math.sqrt(scr_x*scr_y/(2560*1600))
        res_y = res_x
        # resize 
        targets = ['win_x', "win_y", "gap", "het", "srh_r"]
        default_size = [1600,900,60,60,80]
        base_d = {}
        for i, target_i in enumerate(targets):
            value_i = config.get(('Common','Size',target_i),default_size[i])
            value_f = int(res_x*value_i)
            base_d[target_i] = value_f
        base_d = base_d | {'scr_x':scr_x, 'scr_y':scr_y, 'res_x':res_x, 'res_y':res_y}
        for key_i, value_i in config.items():
            if "Size" in key_i:
                config[key_i] = Config_Manager._str2int(value_i, base_d)
        return config
    
    def _calculate_legacy(self):
        self.scr_x, self.scr_y = get_screen_size('pixel')
        res_x = math.sqrt(self.scr_x*self.scr_y/(2560*1600))
        res_y = res_x
        # resize 
        targets = ['win_x', "win_y", "gap", "het", "srh_r"]
        for target_i in targets:
            value_i = self.config[('Common','Size',target_i)]
            value_f = int(res_x*value_i)
            self.config[('Common','Size',target_i)] = value_f
            setattr(self, target_i, value_f)
        
        for key_i, value_i in self.config.items():
            if "Size" in key_i:
                self.config[key_i] = self._str2int(value_i)

    @staticmethod
    def _str2int(input_f:Union[list, str], base_d:dict):
        scr_x, scr_y, win_x, win_y, gap, het, srh_r= symbols('scr_x scr_y win_x win_y gap het srh_r')
        values = {
                scr_x: base_d['scr_x'],
                scr_y: base_d['scr_y'],
                win_x: base_d['win_x'],
                win_y: base_d['win_y'],
                gap: base_d['gap'],
                het: base_d['het'],
                srh_r: base_d['srh_r'],
                }
        if isinstance(input_f, list):
            results = [int(sympify(expr).evalf(subs=values)) for expr in input_f]
            return results
        elif isinstance(input_f, str):
            return int(sympify(input_f).evalf(subs=values))
        else:
            return input_f
    
    def group_chose(self, mode="_", widget="_", obj="_"):
        self.mode = mode if mode != "_" else self.mode
        self.widget = widget if widget != "_" else self.widget
        self.obj = obj if obj!="_" else self.obj
        return self
        
    def get(self, name_f:str, mode:str="_", widget:str="_", obj:str="_", default_v='^default_for_get_func$',ae:bool=True):
        mode = mode if mode!="_" else self.mode
        widget = widget if widget!="_" else self.widget
        obj = obj if obj!="_" else self.obj
        args_a = [i for i in [mode, widget, obj, name_f] if i != None]
        args_a = atuple(args_a)
        out_a = self.config[args_a]
        if ae:
            return self.after_process(args_a, out_a)
        else:
            return out_a

    def get2(self, paras:tuple)->tuple:
        para_t = self.pre
        for para_i in paras:
            para_t.append(para_i)
        return tuple(para_t)
    
    def set_pre(self, paras:tuple):
        self.pre = []
        for para_i in paras:
            self.pre.append(para_i)
    
    def __getitem__(self, key):
        if isinstance(key, atuple):
            out_a = self.config[key]
            if out_a is None:
                return out_a 
            else:
                return self.after_process(key, out_a)
        else:
            return self.get(key)

    def after_process(self, args_a:tuple, target_f):
        if "path" in args_a:
            if isinstance(target_f, list):
                out_l = []
                for i in target_f:
                    if os.path.isabs(i):
                        out_l.append(i)
                    else:
                        out_l.append(str((pathlib.Path(self.wkdr)/pathlib.Path(i)).resolve()))
                return out_l
            elif isinstance(target_f, str):
                if os.path.isabs(target_f):
                    return target_f
                else:
                    return str((pathlib.Path(self.wkdr)/pathlib.Path(target_f)).resolve())
            else:
                return target_f
        elif "font" in args_a:
            font_dict = {i[0]:i[1] for i in target_f}
            return font_get(font_dict)
        else:
            return target_f

class UIData(object):
    def __init__(self, index:int, key:atuple|alist[atuple], action:callable, 
                 type:Literal[None, 'size', 'font', 'icon', 'config', 'height','margin','unpack']| Literal[None, 'size', 'font', 'icon', 'config', 'height','margin','unpack'], value_t, value_ae):
        self.index = index
        self.key = key
        self.action = action
        self.type = type
        self.value_t = value_t
        self.value_ae = value_ae

class UIUpdater(QObject):
    ui_set_l = []
    update_task=Signal(dict)
    @classmethod
    def _primary_init(cls,config:Config_Manager):
        cls.config_manager:Config_Manager = config.deepcopy()
        cls.config:dict = copy.deepcopy(cls.config_manager.config)
    
    @classmethod
    def action(cls, key_f:atuple|alist[atuple], action_f:callable, type_f:alist[Literal[None, 'size', 'font', 'icon', 'config', 'height','margin','unpack']| Literal[None, 'size', 'font', 'icon', 'config', 'height','margin','unpack']]=None):
        value_t = cls._getValue(key_f, cls.config)
        if isinstance(key_f, atuple):
            atuple_check = True
        elif isinstance(key_f, alist):
            atuple_check = True
            for i in key_f:
                if not isinstance(i, atuple):
                    atuple_check = False
                    break
        else:
            atuple_check = False
        
        if not isinstance(value_t, alist):
            if not type_f:
                value_ae = value_t
            else:
                value_ae = cls._value_ae(cls, value_t, type_f)
        else:
            if not type_f:
                value_ae = value_t
            else:
                value_ae = [cls._value_ae(cls, value_t[i], type_f[i]) for i in range(len(value_t))]

        match type_f:
            case _ if isinstance(key_f, alist):
                action_f(*value_ae)
            case 'margin':
                action_f(*value_ae)
            case 'unpack':
                action_f(*value_ae)
            case _:
                if value_ae:
                    action_f(value_ae)
        return atuple_check, value_t, value_ae
    @classmethod
    def get(cls, key_f:atuple|alist[atuple], default_v=None):
        if isinstance(key_f, atuple):
            value_t = cls.config[key_f]
            if not value_t:
                return default_v
            else:
                return value_t
        elif isinstance(key_f, alist):
            value_l = []
            for i in key_f:
                if isinstance(i, atuple):
                    value_l.append(cls.get(i, default_v))
                else:
                    value_l.append(default_v)
            return value_l
        else:
            warnings.warn(f"UIUpdater.get: Invalid key type: {key_f}")
            return default_v
    @classmethod
    def set(cls, key_f:Union[atuple,alist],action_f:callable,
             type_f:Union[alist[Literal[None, 'size', 'font', 'icon', 'config', 'height']], 
                          Literal[None, 'size', 'font', 'icon', 'config', 'height','margin','unpack']]=None):
        atuple_check, value_t, value_ae = cls.action(key_f, action_f, type_f)
        if atuple_check:
            data_c = UIData(index=len(cls.ui_set_l), key=key_f, action=action_f, type=type_f, value_t=value_t, value_ae=value_ae)
            #cls.ui_set_l.append({'index':len(cls.ui_set_l),'key':key_f, 'action':action_f, 'type':type_f, 'value':value_t})
            cls.ui_set_l.append(data_c)
        return value_ae
    
    def __init__(self):
        super().__init__()
        self.update_delay = QTimer()
        self.update_delay.setSingleShot(False)
        self.update_delay.timeout.connect(self.on_yaml_change)
        self.init_watcher()

    def init_watcher(self):
        self.watcher = QFileSystemWatcher([self.config_manager.yaml_path])
        self.watcher.fileChanged.connect(self.restart_timer)  # 连接文件变化信号
        
    def restart_timer(self):
        self.update_delay.start(500)
    
    def on_yaml_change(self):
        self.update_delay.stop()
        try:
            yml_file0 = yml.read(self.config_manager.yaml_path)
            yml_file1 = dicta.flatten_dict(yml_file0)
            yml_file2 = self._calSize(yml_file1)
            yml_file3 = dicta.unflatten_dict(yml_file2)
        except Exception as e:
            warnings.warn(f"Yaml file read failed: {e}")
            return
        if not yml_file3:
            return
        self._updateUI(adict(yml_file3))
        
    
    def _calSize(self, config:dict):
        config_r = copy.deepcopy(config)
        scr_x, scr_y = get_screen_size('pixel')
        res_x = math.sqrt(scr_x*scr_y/(2560*1600))
        res_y = res_x
        # resize 
        targets = ['win_x', "win_y", "gap", "het", "srh_r"]
        default_size = [1600,900,60,60,80]
        base_d = {}
        for i, target_i in enumerate(targets):
            value_i = config.get(atuple('Common','Size',target_i),default_size[i])
            value_f = int(res_x*value_i)
            base_d[target_i] = value_f
        base_d = base_d | {'scr_x':scr_x, 'scr_y':scr_y, 'res_x':res_x, 'res_y':res_y}
        for key_i, value_i in config.items():
            if "Size" in key_i:
                config_r[key_i] = self._str2int(value_i, base_d)
        return config_r
    def _str2int(self, input_f:Union[list, str], base_d:dict):
        scr_x, scr_y, win_x, win_y, gap, het, srh_r= symbols('scr_x scr_y win_x win_y gap het srh_r')
        values = {
                scr_x: base_d['scr_x'],
                scr_y: base_d['scr_y'],
                win_x: base_d['win_x'],
                win_y: base_d['win_y'],
                gap: base_d['gap'],
                het: base_d['het'],
                srh_r: base_d['srh_r'],
                }
        if isinstance(input_f, list):
            results = [int(sympify(expr).evalf(subs=values)) for expr in input_f]
            return results
        elif isinstance(input_f, str):
            return int(sympify(input_f).evalf(subs=values))
        else:
            return input_f

    def _updateUI(self, yml_file:dict):
        for order_i in range(len(self.ui_set_l)):
            i:UIData = self.ui_set_l[order_i]
            # read the value from the new yaml file
            if isinstance(i.key, atuple):
                value_new = yml_file[i.key]
                if value_new is None:
                    warnings.warn(f"Key {i.key} , func {i.action}not found in new yaml file")
                    continue
                elif value_new == i.value_t:
                    continue
            elif isinstance(i.key, alist):
                value_new = alist()
                for i_f, key_i in enumerate(i.key):
                    vi = yml_file[key_i]
                    if vi is None:
                        warnings.warn(f"Key {key_i} not found in new yaml file")
                    value_new.append(vi)
            else:
                warnings.warn(f"Invalid key type: {i.key}")
                continue
            
            if i.value_t == value_new:
                continue

            if isinstance(value_new, alist):
                value_ae = alist()
                for i_f, value_i in enumerate(value_new):
                    if i.type:
                        value_ae.append(self._value_ae(value_i, i.type[i_f]))
                    else:
                        value_ae.append(value_i)
            else:
                value_ae = self._value_ae(value_new, i.type)
            i.value_ae = value_ae
            #self.update_task.emit(new_dict)
            update_result = self._objUpdate(i)
            # if not update_result:
            #     warnings.warn(f"Update {i['key']} failed: {update_result[1]}")
            # else:
            # self.ui_set_l[order_i]['value'] = value_new

    def _objUpdate(self, dict_f:UIData):
        try:
            action_i = dict_f.action
            type_i = dict_f.type
            value_new = dict_f.value_ae
            match type_i:
                case 'unpack' | 'margin':
                    action_i(*value_new)
                case _ if isinstance(value_new, alist):
                    action_i(*value_new)
                case _:
                    action_i(value_new)
            return True, ''
        except Exception as e:
            print(f"Update {dict_f.key} use {dict_f.action} failed: {e}")
            return False, e

    def _value_ae(self, value_i, type_f:Literal[None, 'size', 'font', 'icon', 'config', 'height','margin','unpack']):
        match type_f:
            case 'size':
                match value_i:
                    case _ if isinstance(value_i, int):
                        return QSize(value_i, value_i)
                    case _ if isinstance(value_i, list):
                        return QSize(*value_i[:2])
                    case _ if isinstance(value_i, QSize):
                        return value_i
                    case _:
                        return None
            case 'font':
                return font_get(value_i)
            case 'icon':
                return AIcon(value_i)
            case _:
                return value_i
    
    @staticmethod
    def _getValue(key_f, config_f):
        if isinstance(key_f, atuple):
            return config_f[key_f]
        elif isinstance(key_f, alist):
            return alist(UIUpdater._getValue(i, config_f) for i in key_f)
        else:
            return key_f
    


