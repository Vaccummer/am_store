from PySide2.QtWidgets import QApplication
from Scripts.toolbox import QApplication
from launcher_base import BaseLauncher
from Scripts.toolbox import *
from Scripts.launcher_ui import *
from abc import abstractmethod
class UILauncher(BaseLauncher):
    def __init__(self, config: dict, app: QApplication):
        super().__init__(config, app)
        self._init_layout()
        self._mainwindowUI()
        self._initLauncherUI()
        self._initFuncUI()
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
        self.layout_0.setAlignment(Qt.AlignHCenter)
        # top widget
        self.layout_top = amlayoutH()
        # input widget
        self.layout_input = amlayoutH()
        # associate & shortcut widget
        self.stack_ass = QStackedWidget(self)
        #self.layout_ass = amlayoutH()
        add_obj(self.layout_top, self.layout_input, self.stack_ass, parent_f=self.layout_0)
    
    def _mainwindowUI(self):
        self.top_buttons = TopButton(self, self.config)._initbuttons()
        self.switch_button = SwitchButton(self, self.config)
        self.layout_top.addWidget(self.switch_button)
        self.layout_top.addStretch()
        add_obj(*self.top_buttons, parent_f=self.layout_top)
    
    def _initLauncherUI(self):
        self.path_switch_button = PathModeSwitch(self, config=self.config)
        self.host_d = self.path_switch_button.host_d

        self.input_box = InputBox(self, self.config)
        self.search_togle_button =SearchTogleButton(self, self.config)
        button_action = QWidgetAction(self)
        button_action.setDefaultWidget(self.search_togle_button)
        self.input_box.addAction(button_action, QLineEdit.TrailingPosition)
        self.progress_bar = TransferProgress(self, 100, 10)
        self.input_box_layout = amlayoutV(align_v="c", align_h='l', spacing=10)
        self.input_box_widget = QWidget()
        self.input_box_widget.setLayout(self.input_box_layout)
        self.input_box_layout.addWidget(self.input_box)
        # spacer = QSpacerItem(10, self.progress_bar.height(), QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.progress_bar_layout = amlayoutH(align_h='l')
        self.progress_bar_layout.addSpacing(30)
        self.progress_bar_layout.addWidget(self.progress_bar)
        self.progress_bar_layout.addSpacing(30)
        self.input_box_layout.addLayout(self.progress_bar_layout)

        self.shortcut_entry = ShortcutEntry(self, self.config)
        add_obj(self.path_switch_button, self.input_box_widget, self.shortcut_entry, parent_f=self.layout_input)
        # self.layout_input.addWidget(self.path_switch_button)
        # self.layout_input.addWidget(self.input_box_widget)
        # self.layout_input.addWidget(self.shortcut_entry)
        
    def _initFuncUI(self):
        # first layer content
        self.launcher_manager = LauncherPathManager(self.config)
        self.associate_list = AssociateList(config=self.config.deepcopy(), parent=self)
        self.shortcut_button = ShortcutButton(self, self.config.deepcopy())
        self.shortcut_setting = ShortcutSetting(self, self.config.deepcopy())
        self.ass_wd1 = QWidget()
        self.ass_lo1 = amlayoutH('c', 'c', spacing=20)
        self.ass_wd1.setLayout(self.ass_lo1)
        add_obj(self.associate_list, self.shortcut_button, parent_f=self.ass_lo1)
        
        # terminal layer content
        self.terminal = Terminal(config=self.config.deepcopy(), parent=self)
        self.stack_ass.addWidget(self.terminal)
        self.stack_ass.addWidget(self.ass_wd1)

        self.launcher_settings = LauncherSetting(config=self.config.deepcopy(), parent=self, manager=self.launcher_manager)
        self.stack_ass.addWidget(self.launcher_settings)
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # line_edit_width = self.input_box.width()
        # self.progress_bar.setFixedWidth(max(50, line_edit_width - 150))

if __name__ == "__main__":
    app = QApplication([])
    config  = yml.read(r'launcher_cfg_new.yaml')
    launcher = UILauncher(config, app)
    launcher.show()
    sys.exit(app.exec_())
