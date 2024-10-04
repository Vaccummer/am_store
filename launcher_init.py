from PySide2.QtWidgets import QApplication
from Scripts.tools.toolbox import QApplication
from launcher_base import Launcher_Base
from Scripts.tools.toolbox import *
from Scripts.launcher.launcher_ui import *
from abc import abstractmethod

class InitLauncher(Launcher_Base):
    def __init__(self, config: dict, app: QApplication):
        super().__init__(config, app)
    
    def _init_para(self):
        self.mode = "Launcher"
        self.het = self.config.get("het", mode='Common', widget=None, obj="Size")
        self.gap = self.config.get("gap", mode='Common', widget=None, obj="Size")
        self.win_x = self.config.get("win_x", mode='Common', widget=None, obj="Size")
        self.win_y = self.config.get("win_y", mode='Common', widget=None, obj="Size")
        self.srh_r = self.config.get("srh_r", mode='Common', widget=None, obj="Size")
    def _init_associate_list(self):
        self.config.group_chose(mode=self.mode, widget="associate_list")
        self.ass_xlsx_path = self.config.get("settings_xlsx", widget="path", obj=None)
        self.ass_num = self.config.get("max_ass_num", "Common", None, None)

        self.ass_df = excel_to_df(self.ass_xlsx_path, region='A:C')
        self.ass = Associate(self.ass_df, ouput_num_f=self.ass_num)
        self.associate_list = AssociateList(self.ass, config=self.config, parent=self)
    
    def _int_input_box(self):
        self.input_box = InputBox(self, self.config)
    
    def _init_shortcut_entry(self):
        self.shortcut_entry = ShortcutEntry(self, self.config)
    
    def _init_shortcut_button(self):  
        pass