from PySide2.QtWidgets import QApplication
from sympy import Q
from Scripts.toolbox import QApplication
# from launcher_base import BaseLauncher
from Scripts.toolbox import *
from Scripts.launcher_ui import *
from am_store.common_tools import *
from abc import abstractmethod

class BaseLauncher(QMainWindow):
    MODE = "Launcher"
    HOST = 'Local'
    HOST_TYPE = "Local"
    CONNECT = True
    CON_ERROR = ''
    def __init__(self, config:dict, app:QApplication):
        super().__init__()
        self.wkdir = os.getcwd()
        self.config = Config_Manager(wkdir=self.wkdir, 
                                     config=config, 
                                     mode_name=None,
                                     widget_name=None,
                                     obj_name=None,)
        self.app = app
        self._init_para()
        self.createTrayIcon()
        self._mainwindow_set()
        tip = InfoTip(self, "Info", "Test OK", {}, self.config.deepcopy())
        tip.close()
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
        self.tray_icon.setIcon(QIcon(self.config.get(None, "MainWindow", "taskbar_icon", "path")))
        self.tray_icon.setToolTip("Super Launcher")

        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        max_action = QAction("Maximum", self)
        max_action.triggered.connect(self.showMaximized)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.programm_exit)
        restart_action = QAction("Restart", self)
        restart_action.triggered.connect(lambda : self.restart_program(self.config.get(None, "Common", "script_path", None)))
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
        self.setGeometry(*self.config.get('main_window', mode='Launcher', widget=None, obj="Size"))
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("Super Launcher")
        self.setWindowIcon(QIcon(self.config.get(None, "MainWindow", "taskbar_icon", "path")))
    
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
        self.ssh_manager = SshManager(self, self.config)
    
    def tip(self, title:str, prompt_f:str, value_d:dict, default_v):
        keys = list(value_d.keys())
        values = list(value_d.values())
        value_dn = {keys[i]: i for i in range(len(keys)) }
        tip = InfoTip(self, title, prompt_f, value_dn)
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
        self.close_all_tread()
        time.sleep(0.15)
        QApplication.instance().quit()
    
    def restart_program(self, script_path):
        os.system(f"python {script_path}")
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
        # associate & shortcut widget
        self.stack_ass = QStackedWidget(self)
        #self.layout_ass = amlayoutH()
        add_obj(self.layout_top, self.layout_input, self.stack_ass, parent_f=self.layout_0)
    
    def _mainwindowUI(self):
        self.switch_button = SwitchButton(self, self.config)
        self.switch_button.currentIndexChanged.connect(self._change_mode)
        self.shortcut_entry = ShortcutEntry(self, self.config)
        self.top_buttons = TopButton(self, self.config)._initbuttons()
        self.layout_top.addWidget(self.switch_button)
        self.layout_top.addStretch()
        add_obj(self.shortcut_entry, *self.top_buttons, parent_f=self.layout_top)
    
    def _initLauncherUI(self):
        self.path_switch_button = PathModeSwitch(self, config=self.config)
        self.path_switch_button.currentIndexChanged.connect(self._change_host)
        self.input_box = InputBox(self, self.config)
        self.search_togle_button =SearchTogleButton(self, self.config)
        button_action = QWidgetAction(self)
        button_action.setDefaultWidget(self.search_togle_button)
        self.input_box.addAction(button_action, QLineEdit.TrailingPosition)
        
        self.progress_bar = TransferProgress(self, 100, 10)
        self.input_box_layout = amlayoutH(align_v="c", align_h='l', spacing=1)
        self.input_box_layout.setContentsMargins(0, 0, 0, 0)
        self.path_switch_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.input_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        add_obj(self.path_switch_button, self.input_box, parent_f=self.input_box_layout)
        # spacer = QSpacerItem(10, self.progress_bar.height(), QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.progress_layout = amlayoutH(align_h='l')
        #self.progress_bar_layout.addSpacing(30)
        self.progress_layout.addWidget(self.progress_bar)
        self.progress_stack = QStackedWidget(self)
        
        #self.progress_bar_layout.addSpacing(30)
        #self.input_box_layout.addLayout(self.progress_bar_layout)

        add_obj(self.input_box_layout, self.progress_layout, parent_f=self.layout_input)
        #add_obj(self.path_switch_button, self.input_box_widget, parent_f=self.layout_input)
        # self.layout_input.addWidget(self.path_switch_button)
        # self.layout_input.addWidget(self.input_box_widget)
        # self.layout_input.addWidget(self.shortcut_entry)
        
    def _initFuncUI(self):
        # first layer content
        self.launcher_manager = LauncherPathManager(self.config)
        self.associate_list = AssociateList(config=self.config.deepcopy(), parent=self, manager=self.launcher_manager)
        self.shortcut_button = ShortcutButton(self, self.config.deepcopy())
        self.shortcut_setting = ShortcutSetting(self, self.config.deepcopy())
        self.shortcut_setting.showWin()
        self.ass_wd1 = QWidget()
        self.ass_lo1 = amlayoutH('c', 'c', spacing=20)
        self.ass_wd1.setLayout(self.ass_lo1)
        add_obj(self.associate_list, self.shortcut_button, parent_f=self.ass_lo1)
        
        # terminal layer content
        self.terminal = Terminal(config=self.config.deepcopy(), parent=self)
        
        self.launcher_settings = LauncherSetting(config=self.config.deepcopy(), parent=self, manager=self.launcher_manager)
        self.stack_ass.addWidget(self.ass_wd1)
        self.stack_ass.addWidget(self.terminal)
        self.stack_ass.addWidget(self.launcher_settings)
        self.stack_ass.setCurrentIndex(0)
    
    @staticmethod
    def _change_mode(self, index_n):
        pass
    @staticmethod
    def _change_host(self, index_n):
        pass

class ControlLauncher(UILauncher):
    def __init__(self, config: dict, app: QApplication):
        super().__init__(config, app)
        self.start_maintainer()
        self._obj_connect()
    
    def _change_mode(self, index_n:int):
        self.stack_ass.setCurrentIndex(index_n)
    
    def _change_host(self, index_n:int):
        host_n = self.path_switch_button.itemText(index_n)
        host_type = self.ssh_manager.get_config(host_n)['type']
        self.HOST = host_n
        self.HOST_TYPE = host_type
        if host_type == 'Local':
            self.path_switch_button._setStyle(0)

            self.CONNECT = True
            return
        elif host_type == 'WSL':
            if os.path.exists(self.ssh_manager.get_config(host_n)['config']['path']):
                self.path_switch_button._setStyle(0)
                self.CONNECT = True
                return
            else:
                out_f = self.tip('Error', f"{host_n} WSL not Exists!", {'OK':-1},-1)
                self.path_switch_button._setStyle(2)
                self.CONNECT = False
                return
        self.CONNECT = None
        host_dt = self.ssh_manager.get_config(host_n)['config']
        if host_dt:
            self.path_switch_button._setStyle(1)
            self.thread = WorkerThread(self._cre_connection, host_dt)
            self.thread.finished_signal.connect(self._connection_check)
            self.thread.start()
        else:
            self.path_switch_button._setStyle(2)
            self.CONNECT = False
        # thread_i = WorkerThread(self.ssh_manager.connect, self.HOST)
        #self.ssh_manager.connect(self.HOST)
        # thread_i.error_signal.connect(self.handle_thread_error)
        # thread_i.start()
    
    def handle_thread_error(self, error_message):
        print(error_message)

    def start_maintainer(self):
        self.maintainer = ConnectionMaintainer(self.config)
        self.maintainer.output.connect(self._connection_check)
        self.maintainer.start()
    
    def close_all_tread(self):
        self.maintainer.stop()

    def refresh_connect(self):
        config_t = self.ssh_manager.get_config(self.HOST)['config']
        data_t = {'HOST': self.HOST, 'HOST_TYPE': self.HOST_TYPE, 'host_config': config_t, 'CONNECT': False}
        self.maintainer.data_updated.emit(data_t)

    def _obj_connect(self):
        self.input_box.textChanged.connect(self._input_change)
        self.input_box.key_press.connect(self._input_box_signal_process)
    
    @Slot(dict)
    def _input_box_signal_process(self, input_f:Dict[Literal['key', 'text', 'type'], str]):
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
    
    
    @staticmethod
    def _cre_connection(host_paras:dict):
        server = paramiko.SSHClient()
        server.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        server.connect(host_paras['HostName'], 
                        port=int(host_paras.get('port', 22)), 
                        username=host_paras.get('User', os.getlogin()), 
                        password=host_paras.get('Password', ''),
                        timeout=5)
        stfp = server.open_sftp()
        return (server, stfp)
    
    def _connection_check(self, result):
        sign_f, con = result
        if not sign_f:
            self.path_switch_button._setStyle(2)
            self.CONNECT = False
            self.CON_ERROR = con
        else:
            self.path_switch_button._setStyle(0)
            self.CONNECT = True
            self.CON_ERROR = ''
            self.ssh_manager.server = con[0]
            self.ssh_manager.stfp = con[1]


if __name__ == "__main__":
    # QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app = QApplication([])
    config  = yml.read(r'launcher_cfg_new.yaml')
    launcher = ControlLauncher(config, app)
    launcher.show()
    sys.exit(app.exec_())
