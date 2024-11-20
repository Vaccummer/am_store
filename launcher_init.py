from PySide2.QtWidgets import QApplication
from Scripts.tools.toolbox import QApplication
from launcher_base import BaseLauncher
from Scripts.tools.toolbox import *
from Scripts.launcher.launcher_ui import *
from abc import abstractmethod

class UILauncher(BaseLauncher):
    def __init__(self, config: dict, app: QApplication):
        super().__init__(config, app)
        self._init_layout()
        self._mainwindowUI()
        self._initLauncherUI()
        self.setGeometry(*self.config.get('main_window', mode='Launcher', widget=None, obj="Size"))
    @abstractmethod
    def launch(self):
        # recive para/file path to launch certain file
        pass
    @abstractmethod
    def reload_shortcutbutton(self):
        pass
    
    def _init_layout(self):
        ## main widget
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.layout_0 = QVBoxLayout(self.central_widget)

        # top widget
        self.layout_top = QHBoxLayout()
        self.layout_top.setAlignment(Qt.AlignHCenter)
        self.widget_top = QWidget()
        self.layout_0.addLayout(self.layout_top)

        # input widget
        self.layout_input = QHBoxLayout()
        self.widget_input = QWidget()
        self.layout_0.addLayout(self.layout_input)

        # associate & shortcut widget
        self.layout_ass = QHBoxLayout()
        self.widget_ass = QWidget()
        self.layout_0.addLayout(self.layout_ass)
    
    def _mainwindowUI(self):
        self.top_button = TopButton(self, self.config)
        self.switch_button = SwitchButton(self, self.config)
        self.layout_top.addWidget(self.switch_button)
        self.layout_top.addStretch()
        self.layout_top.addWidget(self.top_button)
    
    def _initLauncherUI(self):
        self.path_switch_button = PathModeSwitch(self, config=self.config, mode_list=["Local", "V100s"])

        self.input_box = InputBox(self, self.config)
        self.search_togle_button =SearchTogleButton(self, self.config)
        button_action = QWidgetAction(self)
        button_action.setDefaultWidget(self.search_togle_button)
        self.input_box.addAction(button_action, QLineEdit.TrailingPosition)
        self.shortcut_entry = ShortcutEntry(self, self.config)
        self.layout_input.addWidget(self.path_switch_button)
        self.layout_input.addWidget(self.input_box)
        self.layout_input.addWidget(self.shortcut_entry)

        self.associate_list = AssociateList(self.ass, config=self.config, parent=self)
        self.shortcut_button = ShortcutButton(self, self.config)
        self.shortcut_setting = ShortcutSetting(self, self.config)
        self.layout_ass.addWidget(self.associate_list)
        self.layout_ass.addWidget(self.shortcut_button)
        
    def _initSearcherUI(self):
        pass

if __name__ == "__main__":
    app = QApplication([])
    config  = yml.read(r'launcher_cfg_new.yaml')
    launcher = UILauncher(config, app)
    launcher.show()
    sys.exit(app.exec_())
