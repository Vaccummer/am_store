from enum import Enum
from sympy import use
import varname
from rich.emoji import Emoji
import inspect
import terminal_ouput_color as toc
from dataclasses import dataclass
from typing import Literal
import time
import logging
import sys
from typing import Callable, Any
import re

@dataclass
class LogConfig:
    DEBUG:Emoji = Emoji("wrench", variant='emoji')
    INFO:Emoji = Emoji("rocket", variant='emoji')
    WARNING:Emoji = Emoji("warning", variant='emoji')
    ERROR:Emoji = Emoji("cross_mark", variant='emoji')
    CRITICAL:Emoji = Emoji("fire", variant='emoji')
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



class LogLevel(Enum):
    DEBUG:int = 0
    INFO:int = 10
    WARNING:int = 20
    ERROR:int = 30
    CRITICAL:int = 40

level_dict = {
    LogLevel.DEBUG: "DEBUG",
    LogLevel.INFO: "INFO",
    LogLevel.WARNING: "WARNING",
    LogLevel.ERROR: "ERROR",
    LogLevel.CRITICAL: "CRITICAL"
}

LogLevel = LogLevel


@dataclass
class LogInfo:
    type:LogLevel
    message:str=""
    trigger_time:float=0.0
    filepath:str = ""
    lineno:int = 0
    line:str = ""
    exception:Exception = None

class AmLogger:
    def __init__(self, log_path:str, print_level:LogLevel=LogLevel.DEBUG, file_level:LogLevel=LogLevel.DEBUG, 
                 use_rich:bool=True,color_config:LogConfig=LogConfig()):
        self.color_config = color_config
        self.print_level = print_level
        self.file_level = file_level
        self.callback = None
        self._start_time = time.time()
        self.log_cache = []
        self.log_path = log_path
        self._init()
        try:
            import rich
            from rich.console import Console
            self.console = Console(highlight=False)
            self.print = self.console.print
            self.use_rich = True
        except Exception as e:
            self.console = None
            self.use_rich = False
            self.print = print

    def _init(self):
        time_n = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self._start_time))
        str_to_write = f"Programm started at {time_n}\n"
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(str_to_write)

    def __del__(self):
        time_start = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self._start_time))
        time_n = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        total_time = time.time()-self._start_time

        str_to_write = f"Programm terminated at {time_n}\n"
        str_to_write += f"Conducted for {total_time:.2f} seconds\n"
        str_to_write += "="*150+'\n'
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(str_to_write)

    def setPrintLevel(self, level:LogLevel):
        self.print_level = level

    def setFileLevel(self, level:LogLevel):
        self.file_level = level

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
        str_terminal = self._getFormatStr(log_info)
        self.print(str_terminal)
        str_file = self._getLogStr(log_info)
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(str(self.console.render_str(str_terminal))+"\n")
        
        if self.callback:
            try:
                self.callback(log_info, str_terminal, str_file)
            except Exception as e:
                pass

    def _getFormatStr(self, log_info:LogInfo)->str:
        # time:str = "\033[92m"
        # filepath:str = "\033[92m"
        # lineno:str = "\033[92m"
        # line:str = "\033[92m"
        # message:str = "\033[92m"
        str_out = ""
        level_name = level_dict[log_info.type]

        time_str = time.strftime("%H:%M:%S", time.localtime())
        str_out += f"{self.color_config.time}{time_str}{self.color_config.STOP}"

        level_format = getattr(self.color_config, f"{level_name}")
        if isinstance(level_format, Emoji):
            str_out += str(level_format)
        else:
            str_out += f"{level_format}[{level_name}]{self.color_config.STOP}"



        exc = log_info.exception
        exc_info = str(exc) if str(exc) else log_info.message
        if exc:
            str_out += f'  {self.color_config.keyword}Raise{self.color_config.STOP} {self.color_config.exception}{type(exc).__name__}:{self.color_config.STOP}'
            str_out += f'{self.color_config.message}{exc_info}{self.color_config.STOP}'
        else:

            str_out += f' {self.color_config.message}{log_info.message}{self.color_config.STOP}'
        
        str_out += f" {self.color_config.arrow}->{self.color_config.STOP}"
        str_out += f' {self.color_config.filepath}"{log_info.filepath}"{self.color_config.STOP}:{self.color_config.lineno}{log_info.lineno}{self.color_config.STOP}'

        return str_out

    def _getLogStr(self, log_info:LogInfo)->str:
        str_out = ""
        level_name = level_dict[log_info.type]
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        exc = log_info.exception

        if exc:
            str_out += f'[{level_name}] {time_str} At "{log_info.filepath}", line {log_info.lineno}, raise {type(exc).__name__}("{str(exc)}"). {log_info.message}'
        else:
            str_out += f'[{level_name}] {time_str} At "{log_info.filepath}", line {log_info.lineno}: {log_info.line}'


        return str_out

    def debug(self, message:str, exc:Exception=None):
       self._log(LogLevel.DEBUG, message, exc)
   
    def info(self, message:str, exc:Exception=None):
       self._log(LogLevel.INFO, message, exc)
   
    def warning(self, message:str, exc:Exception=None):
       self._log(LogLevel.WARNING, message, exc)
   
    def error(self, message:str, exc:Exception=None):
       self._log(LogLevel.ERROR, message, exc)

    def critical(self, message:str, exc:Exception=None):
       self._log(LogLevel.CRITICAL, message, exc)
   


if __name__ == "__main__":
    logger = get_logger("test.log", "DEBUG")
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")

    logger.critical("This is a critical message")

