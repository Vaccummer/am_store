import os
import re
path = r'\\wsl.localhost\Ubuntu-24.04/home/am'
path2 = r'C:\$WINDOWS.~BT'
pattern_f = r'^[~./\\]|^[a-zA-Z]:\\+'

for root, dirs, files in os.walk(path):
    print(root)