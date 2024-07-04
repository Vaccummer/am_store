import os
import subprocess

def update():
    repo_path = "https://github.com/Vaccummer/am_store.git"
    save_path = os.path.realpath(__file__)
    pro_dir = os.path.dirname(save_path)
    os.rename(pro_dir, pro_dir+"_bak")
    download_result = subprocess.run(["git", "fetch", "origin"], check=True, text=True, capture_output=True)
    reset_result = subprocess.run(["git", "reset", "--hard", "origin/main"], check=True, text=True, capture_output=True)
    if download_result.returncode == 0 and reset_result.returncode == 0:
        print("Am_Store updated success!")
    else:
        print("Am_Store updated failed!")
