from enum import IntEnum
import inspect
from ..ConsoleCustom.config import *
from dataclasses import dataclass
import time
from typing import Callable, Any
import os
import atexit

@dataclass
class LogConfig:
    DEBUG:tuple = ("color", "[#0000FF bold]")
    INFO:tuple = ("color", "[#00CED1 bold]")
    WARNING:tuple = ("color", "[#FFA500 bold]")
    ERROR:tuple = ("color", "[#C70C0C bold]")
    CRITICAL:tuple = ("color", "[#FF0000 bold]")
    STOP:str = "[/]"

    text:str = "[#DAE1E2]"
    time:str = "[#04485B]"
    arrow:str = "[bold #04485B]"
    filepath:str = "[#045B04 italic]"
    lineno:str = "[#045B04 italic]"
    message:str = "[#DAE1E2 italic]"
    exception:str = "[#C70C0C bold]"
    keyword:str = "[#D97C0B]"
    exception_info:str = "[#C70C0C bold]"

class LogLevel(IntEnum):
    DEBUG:int = 0
    INFO:int = 10
    WARNING:int = 20
    ERROR:int = 30
    CRITICAL:int = 40

@dataclass
class LogInfo:
    type:LogLevel
    message:str=""
    trigger_time:float=0.0
    filepath:str = ""
    lineno:int = 0
    line:str = ""
    exception:Exception = None

level_dict = {
    LogLevel.DEBUG: "DEBUG",
    LogLevel.INFO: "INFO",
    LogLevel.WARNING: "WARNING",
    LogLevel.ERROR: "ERROR",
    LogLevel.CRITICAL: "CRITICAL"
}

class AmLogger:
    def __init__(self, log_path:str, print_level:LogLevel=LogLevel.DEBUG, file_level:LogLevel=LogLevel.DEBUG, 
                 callback_level:LogLevel=LogLevel.DEBUG, color_config:LogConfig=LogConfig()):
        assert log_path, "log_path is required"
        log_path = os.path.abspath(log_path)
        if not os.path.exists(os.path.dirname(log_path)):
            raise FileNotFoundError('"log_path" requires a valid directory!' )
        self.log_path = log_path
        self.color_config = color_config
        self.print_level = print_level
        self.file_level = file_level
        self.callback_level = callback_level
        self.callback = None
        self._start_time = time.time()
        self.log_cache = []
        self._init()
        try:
            from rich.console import Console
            self.console = Console(highlight=False)
            self.print = self.console.print
        except ImportError:
            raise ImportError('rich is not installed, use "pip install rich" to install it!')
        atexit.register(self._close)
        
    def _init(self):
        time_n = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self._start_time))
        str_to_write = f"Programm started at {time_n}\n"
        self.write(str_to_write)
        self.max_name_len = max(len(i) for i in level_dict.values())+2
    
    def _close(self):
        time_n = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        total_time = time.time()-self._start_time
        str_to_write = f"Programm terminated at {time_n}\n"
        str_to_write += f"Conducted for {total_time:.2f} seconds\n"
        str_to_write += "="*120+'\n'
        import builtins
        with builtins.open(self.log_path, "a", encoding="utf-8")as f:
            f.write(str_to_write)

    def setPrintLevel(self, level:LogLevel):
        self.print_level = level

    def setFileLevel(self, level:LogLevel):
        self.file_level = level

    def setCallbackLevel(self, level:LogLevel):
        self.callback_level = level

    def setCallback(self, callback:Callable[[LogInfo, str, str], Any]):
        self.callback = callback

    def _log(self, level:LogLevel, msg:str, exc:Exception=None):
        frame = inspect.stack()[2]  
        frame_info = inspect.getframeinfo(frame[0])  
        caller_filename = frame_info.filename  
        caller_lineno = frame_info.lineno  
        caller_line = frame_info.code_context[0].strip()  
        log_info = LogInfo(level, msg, time.time(), caller_filename, caller_lineno, caller_line, exc)
        try:
            self.log_cache.append(log_info)
        except Exception as e:
            pass
        
        if level > self.print_level:
            str_terminal = self._getFormatStr(log_info)
            self.print(str_terminal)
        if level > self.file_level:
            str_file = self._getLogStr(log_info)
            self.write(str_file+'\n')
        if self.callback:
            if level > self.callback_level:
                try:
                    self.callback(log_info, str_terminal, str_file)
                except Exception as e:
                    pass

    def _getFormatStr(self, log_info:LogInfo)->str:
        str_out = ""

        level_name = level_dict[log_info.type]

        time_str = time.strftime("%H:%M:%S", time.localtime())
        str_out += f"{self.color_config.time}{time_str}{self.color_config.STOP}"

        level_format = getattr(self.color_config, f"{level_name}")
        if level_format[0] == "emoji":
            str_out += f"{level_format[1]}"
        else:
            level_n = f'[{level_name}]'
            level_n1 = level_n + ' '*(self.max_name_len-len(level_n))
            str_out += f"{level_format[1]}{level_n1}{self.color_config.STOP}"

        exc = log_info.exception
        exc_info = str(exc) if str(exc) else log_info.message
        if exc:
            str_out += f' {self.color_config.keyword}Raise{self.color_config.STOP} {self.color_config.exception}{type(exc).__name__}:{self.color_config.STOP}'
            str_out += f'{self.color_config.message}{exc_info}{self.color_config.STOP}'
        else:

            str_out += f' {self.color_config.message}{log_info.message}{self.color_config.STOP}'
        
        str_out += f" {self.color_config.arrow}->{self.color_config.STOP}"
        str_out += f' {self.color_config.filepath}"{log_info.filepath}"{self.color_config.STOP}:{self.color_config.lineno}{log_info.lineno}{self.color_config.STOP}'

        return str_out

    def _getLogStr(self, log_info:LogInfo)->str:
        str_out = ""
        level_name = level_dict[log_info.type]
        level_format = getattr(self.color_config, f"{level_name}")
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        exc = log_info.exception

        if level_format[0] == "emoji":
            level_str = f"{level_format[1]}"
        else:
            level_n = f"[{level_name}]"
            level_n1 = level_n + ' '*(self.max_name_len-len(level_n))
            level_str = f"{level_n1}"

        if exc:
            str_out += f'{time_str} {level_str} Raise {type(exc).__name__}("{str(exc)}"), {log_info.message} -> "{log_info.filepath}":{log_info.lineno}, {log_info.line}'
        else:
            str_out += f'{time_str} {level_str} {log_info.message} -> "{log_info.filepath}":{log_info.lineno}, {log_info.line}'
        return str_out

    def write(self, text_f:str)->None:
        r'''
        write won't include \n
        '''
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(text_f)

    def debug(self, message:str, exc:Exception=None)->None:
       self._log(LogLevel.DEBUG, message, exc)

    def info(self, message:str, exc:Exception=None)->None:
       self._log(LogLevel.INFO, message, exc)
   
    def warning(self, message:str, exc:Exception=None)->None:
       self._log(LogLevel.WARNING, message, exc)
   
    def error(self, message:str, exc:Exception=None)->None:
       self._log(LogLevel.ERROR, message, exc)

    def critical(self, message:str, exc:Exception=None)->None:
       self._log(LogLevel.CRITICAL, message, exc)
   
def get_logger(log_path:str, print_level:LogLevel=LogLevel.DEBUG, file_level:LogLevel=LogLevel.DEBUG, 
                 callback_level:LogLevel=LogLevel.DEBUG, color_config:LogConfig=LogConfig())->AmLogger:
    return AmLogger(log_path, print_level, file_level, callback_level, color_config)

if __name__ == "__main__":
    logger = get_logger("test.log")
    logger.debug("test")
    logger.info("test")
    logger.warning("test")
    logger.error("test")
    logger.critical("test")


