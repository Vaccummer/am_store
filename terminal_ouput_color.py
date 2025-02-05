from dataclasses import dataclass
import traceback

@dataclass
class TerminalErrorColorConfig:
    error:tuple = (('color', '#DCD7D7'), ('bold', True), ('italic', False), ('underline', False), ('strike', False))

    message:tuple = (('color', '#00CED1'), ('bold', False), ('italic', True), ('underline', False), ('strike', False))

    date:tuple = (('color', '#1B55DD'), ('bold', False), ('italic', True), ('underline', False), ('strike', False))

    time:tuple = (('color', '#10E46C'), ('bold', False), ('italic', True), ('underline', False), ('strike', False))

    text:tuple = (('color', '#DCD7D7'), ('bold', False), ('italic', False), ('underline', False), ('strike', False))

    filename:tuple = (('color', '#189731'), ('bold', False), ('italic', False), ('underline', False), ('strike', False))

    lineno:tuple = (('color', '#00FF00'), ('bold', False), ('italic', False), ('underline', False), ('strike', False))

    name:tuple = (('color', '#0000FF'), ('bold', False), ('italic', False), ('underline', False), ('strike', False))

    line:tuple = (('color', '#E6E0E0'), ('bold', False), ('italic', False), ('underline', False), ('strike', False))

    locals:tuple = (('color', '#000000') , ('bold', False), ('italic', False), ('underline', False), ('strike', False))

@dataclass
class WarningColorConfig:
    warning:tuple = (('color', '#FFA500'), ('bold', True), ('italic', False), ('underline', False), ('strike', False))

    message:tuple = (('color', '#FFA500'), ('bold', False), ('italic', True), ('underline', False), ('strike', False))

    date:tuple = (('color', '#FFA500'), ('bold', False), ('italic', True), ('underline', False), ('strike', False))

@dataclass
class TracebackInfo:
    filename:str
    lineno:int
    name:str
    line:str
    locals:dict

def error_format(error_config:TerminalErrorColorConfig, 
                 error_type:str, error_message:str, 
                 start_time:float, end_time:float, traceback_list:list[TracebackInfo])->str:
    pass

