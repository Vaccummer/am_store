import os
import subprocess
import shutil

def update():
    repo_path = "https://github.com/Vaccummer/am_store.git"
    save_path = os.path.realpath(__file__)
    pro_dir = os.path.dirname(save_path)
    os.rename(pro_dir, pro_dir+"_bak")
    download_result = subprocess.run(["git", "fetch", "origin"], check=True, text=True, capture_output=True)
    reset_result = subprocess.run(["git", "reset", "--hard", "origin/main"], check=True, text=True, capture_output=True)
    if download_result.returncode == 0:
        shutil.rmtree(pro_dir+"_bak")
        print("Am_Store updated success!")
    else:
        os.rename(pro_dir+"_bak", pro_dir)
        print("Am_Store updated failed!")
