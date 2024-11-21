import subprocess
from pathlib import Path
import os
path_d = Path(r'C:\Windows\System32')
os.chdir(r'E:\SuperLauncher\icon_extract')
for path_i in path_d.glob("*.dll"):
    dst = r'F:\Windows_Data\Desktop_File\icon_all'
    subprocess.run(f'main.exe {path_i} {dst}', shell=True)
