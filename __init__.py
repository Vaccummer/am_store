# name: am_store
# author: Vaccummer
# date: 2024-07-4
# coding: utf-8
# version: 1.0
# address: https://github.com/Vaccummer/am_store.git
# initialize
from .tools.functions import *
from .tools.classes import *
from .ConsoleCustom.config import *
from .Logger.logger import *
import sys
from functools import partial

def init():
    sys.excepthook = partial(call_back_exception, cf=TerminalErrorColorConfig)

