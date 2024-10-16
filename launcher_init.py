from PySide2.QtWidgets import QApplication
from Scripts.tools.toolbox import QApplication
from launcher_base import BaseLauncher
from Scripts.tools.toolbox import *
from Scripts.launcher.launcher_ui import *
from abc import abstractmethod

class UILauncher(BaseLauncher):
    def __init__(self, config: dict, app: QApplication):
        super().__init__(config, app)
        self._initLauncherUI()
        self.setGeometry(*self.config.get('main_window', mode='Launcher', widget=None, obj="Size"))
    
    @abstractmethod
    def launch(self):
        # recive para/file path to launch certain file
        pass
    @abstractmethod
    def reload_shortcutbutton(self):
        pass

    def _initMainUI(self):
        self.top_button = TopButton(self, self.config)
        self.switch_button = SwitchButton(self, self.config)
    
    def _initLauncherUI(self):
        self.associate_list = AssociateList(self.ass, config=self.config, parent=self)
        self.input_box = InputBox(self, self.config)
        self.shortcut_entry = ShortcutEntry(self, self.config)
        self.shortcut_button = ShortcutButton(self, self.config)
        self.shortcut_setting = ShortcutSetting(self, self.config)
        
    def _initSearcherUI(self):
        pass

if __name__ == "__main__":
    app = QApplication([])
    config  = yml.read(r'E:\Launcher_New\launcher_cfg_new.yaml')
    launcher = UILauncher(config, app)
    launcher.show()
    sys.exit(app.exec_())
