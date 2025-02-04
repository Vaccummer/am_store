import argparse
import pathlib
import os
import zipfile
from tqdm import tqdm
import os
import zipfile
import gzip
import bz2
import tarfile
import rarfile
import py7zr
import lzma
from typing import Literal
from tqdm import tqdm

parser = argparse.ArgumentParser(description="Multi Format Zip Funciton v1.0\n@Vaccummer   https://github.com/Vaccummer",
                                 formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("-p", "--progress", help="1 to show progress, 0 to hide", type=int, default=1)
parser.add_argument("paths", nargs='*', help="One or more file or directory paths to operate on")
args= parser.parse_args()

class AMZIP(object):
    func_dict = {}
    def __init__(self, src:pathlib.Path, 
                        dst:pathlib.Path, 
                        action:Literal['zip', 'unzip'],
                        ext_f:Literal['.tar', '.rar', '.7z', '.xz', '.tar.gz', '.tar.xz'],
                        show_progress:int):
        assert action in ['zip', 'unzip'], "action must be 'zip' or 'unzip'"
        assert ext_f in self.func_dict.keys(), f"ext_f must be in {self.func_dict.keys()}"
        self.show_progress = False if show_progress == 0 else True
        func = self.func_dict.get(ext_f)
        if func is None:
            raise NotImplementedError(f"Function for {ext_f} is not implemented")
        
def unzip(self, src:pathlib.Path, dst:pathlib.Path, format_f:str):
    pass
def zip(src:pathlib.Path, dst:pathlib.Path, format_f:str):
    pass


# 压缩和解压通用函数
def decompress_file(file_path, output_dir):
    # 读取文件扩展名
    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.zip':
        return unzip_file(file_path, output_dir)
    elif ext == '.gz':
        return gunzip_file(file_path, output_dir)
    elif ext == '.bz2':
        return bunzip2_file(file_path, output_dir)
    elif ext == '.tar':
        return untar_file(file_path, output_dir)
    elif ext == '.rar':
        return unrar_file(file_path, output_dir)
    elif ext == '.7z':
        return un7z_file(file_path, output_dir)
    elif ext == '.xz':
        return unxz_file(file_path, output_dir)
    elif ext == '.tar.gz' or ext == '.tgz':
        return untar_gz_file(file_path, output_dir)
    elif ext == '.tar.bz2' or ext == '.tbz2':
        return untar_bz2_file(file_path, output_dir)
    elif ext == '.tar.xz' or ext == '.txz':
        return untar_xz_file(file_path, output_dir)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
# 解压zip文件
def unzip_file(file_path, output_dir):
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        file_list = zip_ref.namelist()
        with tqdm(total=len(file_list), desc=f"Extracting {file_path}") as pbar:
            for file in file_list:
                zip_ref.extract(file, output_dir)
                pbar.update(1)

# 解压gzip文件
def gunzip_file(file_path, output_dir):
    with gzip.open(file_path, 'rb') as f_in:
        out_file = os.path.join(output_dir, os.path.basename(file_path).replace('.gz', ''))
        with open(out_file, 'wb') as f_out:
            total_size = os.path.getsize(file_path)
            with tqdm(total=total_size, unit='B', unit_scale=True, desc=f"Extracting {file_path}") as pbar:
                while chunk := f_in.read(1024):
                    f_out.write(chunk)
                    pbar.update(len(chunk))

# 解压bzip2文件
def bunzip2_file(file_path, output_dir):
    with bz2.open(file_path, 'rb') as f_in:
        out_file = os.path.join(output_dir, os.path.basename(file_path).replace('.bz2', ''))
        with open(out_file, 'wb') as f_out:
            total_size = os.path.getsize(file_path)
            with tqdm(total=total_size, unit='B', unit_scale=True, desc=f"Extracting {file_path}") as pbar:
                while chunk := f_in.read(1024):
                    f_out.write(chunk)
                    pbar.update(len(chunk))

# 解压tar文件
def untar_file(file_path, output_dir):
    with tarfile.open(file_path, 'r') as tar_ref:
        file_list = tar_ref.getnames()
        with tqdm(total=len(file_list), desc=f"Extracting {file_path}") as pbar:
            for member in tar_ref.getmembers():
                tar_ref.extract(member, output_dir)
                pbar.update(1)

# 解压rar文件
def unrar_file(file_path, output_dir):
    with rarfile.RarFile(file_path) as rar_ref:
        file_list = rar_ref.namelist()
        with tqdm(total=len(file_list), desc=f"Extracting {file_path}") as pbar:
            for file in file_list:
                rar_ref.extract(file, output_dir)
                pbar.update(1)

# 解压7z文件
def un7z_file(file_path, output_dir):
    with py7zr.SevenZipFile(file_path, mode='r') as z:
        file_list = z.getnames()
        with tqdm(total=len(file_list), desc=f"Extracting {file_path}") as pbar:
            z.extractall(path=output_dir)
            pbar.update(len(file_list))

# 解压xz文件
def unxz_file(file_path, output_dir):
    with lzma.open(file_path, 'rb') as f_in:
        out_file = os.path.join(output_dir, os.path.basename(file_path).replace('.xz', ''))
        with open(out_file, 'wb') as f_out:
            total_size = os.path.getsize(file_path)
            with tqdm(total=total_size, unit='B', unit_scale=True, desc=f"Extracting {file_path}") as pbar:
                while chunk := f_in.read(1024):
                    f_out.write(chunk)
                    pbar.update(len(chunk))

# 解压tar.gz文件
def untar_gz_file(file_path, output_dir):
    with tarfile.open(file_path, 'r:gz') as tar_ref:
        file_list = tar_ref.getnames()
        with tqdm(total=len(file_list), desc=f"Extracting {file_path}") as pbar:
            for member in tar_ref.getmembers():
                tar_ref.extract(member, output_dir)
                pbar.update(1)

# 解压tar.bz2文件
def untar_bz2_file(file_path, output_dir):
    with tarfile.open(file_path, 'r:bz2') as tar_ref:
        file_list = tar_ref.getnames()
        with tqdm(total=len(file_list), desc=f"Extracting {file_path}") as pbar:
            for member in tar_ref.getmembers():
                tar_ref.extract(member, output_dir)
                pbar.update(1)
def untar_xz_file(file_path, output_dir):
    with tarfile.open(file_path, 'r:xz') as tar_ref:
        file_list = tar_ref.getnames()
        with tqdm(total=len(file_list), desc=f"Extracting {file_path}") as pbar:
            for member in tar_ref.getmembers():
                tar_ref.extract(member, output_dir)
                pbar.update(1)

class AMZIPCLASS(object):
    func_dict = {
        ".zip": _zip,
        ".gz": _gzip,
        ".bz2": _bz2,
        ".tar": _tar,
        ".rar": _rar,
        ".7z": _7z,
        ".xz": _xz,
        ".tar.gz": _tar_gz,
        ".tar.bz2": _tar_bz2,
        ".tar.xz": _tar_xz
    }
    def __init__(self, src, dst, format_i, show_progress):
        self.src = src
        self.dst = dst
        self.format_i = format_i
        self.show_progress = show_progress
        pass
    def zip(self):
        pass
    def unzip(self):
        pass    
if __name__ == "__main__":
    src = pathlib.Path(args.paths[0])
    dst = pathlib.Path(args.paths[1])
    if not src.exists():
        print(f"Error: {src} not found!")
        exit(1)
    
    if src.is_dir():
        format_i = dst.suffix
        if str(dst.stem).endswith(".tar"):
            format_i = ".tar" + format_i
        AMZIPCLASS(src, dst, format_i, args.progress).zip()
        exit(0)
    elif src.is_file():
        format_i = src.suffix
        if str(dst.stem).endswith(".tar"):
            format_i = ".tar" + format_i
        AMZIPCLASS(src, dst, format_i, args.progress).unzip()
        exit(0)
    else:
        print(f"Error: {src} is not a file or directory!")
        exit(1)
    