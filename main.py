from PySide2.QtWidgets import QApplication
from sympy import Q
from Scripts.tools.toolbox import *
from Scripts.ui.launcherUI import *
from Scripts.ui.settingUI import *
from Scripts.ui.custom_widget import *
from Scripts.ui.mainwindowUI import *
from Scripts.tools.toolbox import *
from Scripts.manager.config_ui import *
from abc import abstractmethod
from Scripts.manager.paths_transfer import *

class BaseLauncher(QMainWindow):
    MODE = "Launcher"
    HOST = 'Local'
    HOST_TYPE = "Local"
    CONNECT = True
    CON_ERROR = ''
    def __init__(self, config:Config_Manager, app:QApplication):
        super().__init__()
        self.config = config
        self.app = app
        self._init_para()
        self.createTrayIcon()
        self._mainwindow_set()
        self._load_data()
    # For mouse control
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.isNearEdge(event.pos()):
                self.edge_drag = event.pos()
                self.original_geometry = self.geometry()
                event.accept()
            else:
                x, y, w, h = self.get_geometry(self.switch_button)
                if event.y() >y+h or event.x() > x+w:
                    self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
                    event.accept()
        else:
            super().mousePressEvent(event)
    def mouseMoveEvent(self, event):
        if self.edge_drag:
            self.resizeWindow(event.pos())
        elif self.drag_position and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
        else:
            super().mouseMoveEvent(event)
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = None
            self.edge_drag = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    def isNearEdge(self, pos):
        x, y, w, h = self.get_geometry(self)
        return (
            pos.x() > w - self.edge_threshold or
            pos.y() > h - self.edge_threshold
        )
    def resizeWindow(self, pos):
        diff = pos - self.edge_drag
        if abs(diff.x()) > abs(diff.y()):
            new_width = max(self.original_geometry.width() + diff.x(), self.minimumWidth())
            self.setGeometry(self.original_geometry.x(), self.original_geometry.y(), new_width, self.original_geometry.height())
        else:
            new_height = max(self.original_geometry.height() + diff.y(), self.minimumHeight())
            self.setGeometry(self.original_geometry.x(), self.original_geometry.y(), self.original_geometry.width(), new_height)
    def closeEvent(self, event):
        # rewrite close event
        event.ignore()  # ignore the close event
        self.hide()  # hide the main window
        self.tray_icon.showMessage("Super Launcher", "Main Window is now hidden", QSystemTrayIcon.Information)
    
    def createTrayIcon(self):
        # create taskbar hide icon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(self.config.get(None, "MainWindow", "task_bar_icon")))
        self.tray_icon.setToolTip("Super Launcher")

        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        max_action = QAction("Maximum", self)
        max_action.triggered.connect(self.showMaximized)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.programm_exit)
        restart_action = QAction("Restart", self)
        restart_action.triggered.connect(lambda: self.restart_program(None))
        tray_menu = QMenu()

        tray_menu.addAction(show_action)
        tray_menu.addAction(max_action)
        tray_menu.addAction(restart_action)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.show)
        self.tray_icon.show()
    
    def _init_para(self):
        self.setMinimumSize(350, 350)
        # for mouse click enven judge
        self.drag_position = None
        self.edge_drag = None
        self.edge_threshold = 5

        # init state variable
        self.het = self.config.get("het", mode='Common', widget=None, obj="Size")
        self.gap = self.config.get("gap", mode='Common', widget=None, obj="Size")
        self.win_x = self.config.get("win_x", mode='Common', widget=None, obj="Size")
        self.win_y = self.config.get("win_y", mode='Common', widget=None, obj="Size")
        self.srh_r = self.config.get("srh_r", mode='Common', widget=None, obj="Size")
        self.edge_threshold = int(self.gap/3.5)

        #self.ass_xlsx_path = self.config.get("settings_xlsx", "Launcher", widget="path", obj=None)
        #self.ass_num = self.config.get("max_ass_num", "Common", None, None)
        #self.ass_df = excel_to_df(self.ass_xlsx_path, region='A:D', sheet_name_f='all')
        # self.ass = Associate(self.config)
    
    def _mainwindow_set(self):
        self.setGeometry(*self.config.get('main_window', mode='MainWindow', widget=None, obj="Size"))
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("Super Launcher")
        self.setWindowIcon(QIcon(self.config.get(None, "MainWindow", "task_bar_icon")))
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # 绘制带有圆角和渐变的窗口背景
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(113, 148, 139))
        gradient.setColorAt(1, QColor(162, 245, 224))
        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 20, 20)
    
    def _load_data(self):
        self.launcher_data = LauncherPathManager(self.config)
        self.shortcut_data = ShortcutsPathManager(self.config)
        self.path_manager = PathManager(self, self.config)
    
    def tip(self, title:str, prompt_f:str, value_d:dict, default_v):
        keys = list(value_d.keys())
        values = list(value_d.values())
        value_dn = {keys[i]: i for i in range(len(keys)) }
        tip = InfoTip(title, prompt_f, value_dn, self.config)
        if tip.exec_() == QDialog.Accepted:
            return_i = tip.VALUE
            tip.close()
        else:
            return_i = -10
        if return_i < -2:
            return default_v
        return values[return_i]

    def programm_exit(self):
        ## programm exit
        try:
            self.close_all_tread()
        except Exception as e:
            warnings.warn(f"Error in close thread: {e}")
        time.sleep(0.15)
        QApplication.instance().quit()
    
    def restart_program(self, script_path=None):
        script_path = script_path if script_path else os.path.abspath(__file__)
        subprocess.Popen([sys.executable, script_path])
        self.programm_exit()
    
    @staticmethod
    def get_geometry(window_f):
        geom_f = window_f.geometry()
        return[geom_f.x(), geom_f.y(), geom_f.width(), geom_f.height()]

class UILauncher(BaseLauncher):
    def __init__(self, config: dict, app: QApplication):
        super().__init__(config, app)
        self._init_layout()
        self._mainwindowUI()
        self._initLauncherUI()
        self._initFuncUI()
        self._init_layout_margin()

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
        self.layout_input = amlayoutV()
        self.layout_input.setSpacing(5) 
        # associate & shortcut widget
        self.stack_ass = SmartStackWidget(self)
        #self.layout_ass = amlayoutH()
        add_obj(self.layout_top, self.layout_input, self.stack_ass, parent_f=self.layout_0)
    
    def _mainwindowUI(self):
        # self.switch_button = CustomComboBox()
        self.switch_button = SwitchButton(self, self.config)
        self.MODE = self.switch_button.modes[0]
        self.switch_button.index_changed.connect(self._change_mode)
        # self.shortcut_entry = ShortcutEntry(self)
        self.top_buttons_widget = TopButton(self, self.config)
        # self.top_buttons = TopButton(self, self.config)._initbuttons()
        self.layout_top.addWidget(self.switch_button)
        self.layout_top.addStretch()
        add_obj(self.top_buttons_widget, parent_f=self.layout_top)
    
    def _initLauncherUI(self):
        self.path_switch_button = PathModeSwitch(self, config=self.config)
        self.HOST = self.path_switch_button.getMode(0)
        self.path_switch_button.index_changed.connect(self._change_host)
        self.input_box = InputBox(self, self.config)
        self.search_togle_button = SearchTogleButton(self, self.config, input_box_geometry=self.input_box.geometry())
        #self.search_togle_button =SearchTogleButton(self, self.config)
        # button_action = QWidgetAction(self)
        # button_action.setDefaultWidget(self.search_togle_button)
        # self.input_box.addAction(button_action, QLineEdit.TrailingPosition)
        
        self.progress_bar = ProgressWidget(self)
        self.input_box_layout = amlayoutH(align_v="c", align_h='l', spacing=1)
        self.input_box.geometry_signal.connect(self.search_togle_button._update_geometry)
        self.path_switch_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self.input_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        add_obj(self.path_switch_button, self.input_box, parent_f=self.input_box_layout)
        # spacer = QSpacerItem(10, self.progress_bar.height(), QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.progress_layout = amlayoutH(align_h='l')

        add_obj(self.input_box_layout, self.progress_bar, parent_f=self.layout_input)
    
    def _initFuncUI(self):
        # first layer content
        self.launcher_manager = LauncherPathManager(self.config)
        self.associate_list = AssociateList(config=self.config.deepcopy(), parent=self, manager=self.launcher_manager)
        self.shortcut_button = ShortcutButton(self, self.config.deepcopy())
        self.shortcut_setting = ShortcutSetting(self, self.config.deepcopy())
        self.shortcut_setting.showWin()
        self.ass_wd1 = QWidget()
        self.ass_lo1 = amlayoutH('c', 'c')
        self.ass_wd1.setLayout(self.ass_lo1)
        add_obj(self.associate_list, self.shortcut_button, parent_f=self.ass_lo1)
        
        # terminal layer content
        self.terminal = Terminal(config=self.config.deepcopy(), parent=self)
        
        self.launcher_settings = LauncherSetting(config=self.config.deepcopy(), parent=self, manager=self.launcher_manager)
        self.stack_ass.addWidget(self.ass_wd1)
        self.stack_ass.addWidget(self.terminal)
        self.stack_ass.addWidget(self.launcher_settings)
        self.stack_ass.setCurrentIndex(0)
    
    def _init_layout_margin(self):
        pre = atuple('MainWindow', 'Size', 'layout_margin')
        main_layout = pre|'main_layout'
        up_widget_layout = pre|'up_widget_layout'
        input_and_progress_layout = pre|'input_and_progress_layout'
        ass_and_shortcut_button_layout = pre|'ass_and_shortcut_button_layout'
        stack_widget_layout = pre|'stack_widget_layout'
        UIUpdater.set(main_layout, self.layout_0.setContentsMargins, 'margin')
        UIUpdater.set(up_widget_layout, self.layout_top.setContentsMargins, 'margin')
        UIUpdater.set(input_and_progress_layout, self.layout_input.setContentsMargins, 'margin')
        UIUpdater.set(ass_and_shortcut_button_layout, self.ass_wd1.setContentsMargins, 'margin')
        UIUpdater.set(stack_widget_layout, self.stack_ass.setContentsMargins, 'margin')
    
    @staticmethod
    def _change_mode(self, index_n):
        pass
    @staticmethod
    def _change_host(self, index_n):
        pass

class ControlLauncher(UILauncher):
    def __init__(self, config: dict, app: QApplication):
        super().__init__(config, app)
        self._obj_connect()
    
    def _change_mode(self, index_n:int):
        self.MODE = self.switch_button.modes[index_n]
        self.stack_ass.setCurrentIndex(index_n)
    
    def _change_host(self, index_n:int):
        host_n = self.path_switch_button.getMode(index_n)
        result_i, type_i, error = self.path_manager.change_host(host_n)
        self.HOST = host_n
        self.HOST_TYPE = type_i
        self.CON_ERROR = error
        self.CONNECT = result_i
        if result_i is True:
            self.path_switch_button.setState(0)
        elif result_i is False:
            self.path_switch_button.setState(2)
        else:
            self.path_switch_button.setState(1)
   
    def handle_thread_error(self, error_message):
        print(error_message)

    def close_all_tread(self):
        self.path_manager.maintainer.stop()

    def _obj_connect(self):
        self.input_box.textChanged.connect(self._input_change)
        self.input_box.key_press.connect(self._input_box_signal_process)
        self.path_manager.con_res.connect(self._connection_check)
        self.top_buttons_widget.button_click.connect(self._top_button_click)
    
    @Slot(str)
    def _top_button_click(self, sign:Literal['minimum', 'maximum', 'close', 'entry']):
        match sign:
            case 'entry':
                if self.shortcut_setting.isVisible():
                    return
                self.shortcut_setting = ShortcutSetting(self, self.config.deepcopy())
                self.shortcut_setting.showWin()
    @Slot(dict)
    def _input_box_signal_process(self, input_f:dict[Literal['key', 'text', 'type'], str]):
        event_type = input_f['type']
        text = input_f['text']
        if event_type == 'key_press':
            key = input_f['key']
            match key:
                case Qt.Key_Tab:
                    tab_out = self.associate_list._tab_complete(text)
                    if tab_out:
                        self.input_box.setText(tab_out)
                case Qt.Key_Return, Qt.Key_Enter:
                    self.confirm_input(text)
                    self.input_box.setText('')
                case Qt.Key_Up:
                    pass
                case Qt.Key_Down:
                    pass
                case _:
                    return
        elif event_type == 'file_drop':
            paths_com = " ".join(input_f['paths'])
            if text:
                self.input_box.setText(text+" "+paths_com)
            else:
                self.input_box.setText(paths_com)
        else:
            return
    
    def _input_change(self, text:str):
        if self.MODE == "Launcher":
            self.associate_list.update_associated_words(text)
            driver_parttern = r"^([A-Za-z])[\\]$"
            dirver_match = re.match(driver_parttern, text)
            if dirver_match:
                self.input_box.setText(f"{dirver_match.group(1)}:\\")
                return
    
    @Slot(list)
    def _connection_check(self, result):
        sign_f, error = result
        self.CON_ERROR = error
        if self.CONNECT == sign_f:
            return
        else:
            self.CONNECT = sign_f
        if not sign_f:
            self.path_switch_button.setState(2)
        else:
            self.path_switch_button.setState(0)

    @Slot(dict)
    def _updateUI(self, dict_f:dict):
        try:
            action_i = dict_f['action']
            type_i = dict_f['type']
            value_new = dict_f['value_new']
            match type_i:
                case 'unpack' | 'margin':
                    action_i(*value_new)
                case _:
                    action_i(value_new)
            return True, ''
        except Exception as e:
            return False, e
    @Slot()
    def _refresh_setting(self):
        self._refresh_setting.disconnect()
        self._refresh_setting.connect(self.shortcut_setting.refresh_signal)
        self.shortcut_button.refresh()
if __name__ == "__main__":
    # QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app = QApplication([])
    path_t = os.path.abspath('./launcher_cfg_new.yaml')
    Config_Manager.set_config_path(path_t)
    config = Config_Manager(wkdir=os.getcwd())
    UIUpdater._primary_init(config)
    uiupdater = UIUpdater()
    launcher = ControlLauncher(config, app)
    uiupdater.update_task.connect(launcher._updateUI)
    launcher.show()
    sys.exit(app.exec_())
