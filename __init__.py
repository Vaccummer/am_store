from Main_Init import UILauncher
from PySide2.QtWidgets import QApplication
from launcher_base import BaseLauncher
from Scripts.toolbox import *
from Scripts.launcher_ori import *
from abc import abstractmethod
if __name__ == "__main__":
    app = QApplication([])
    config  = yml.read(r'launcher_cfg_new.yaml')
    launcher = UILauncher(config, app)
    launcher.show()
    sys.exit(app.exec_())