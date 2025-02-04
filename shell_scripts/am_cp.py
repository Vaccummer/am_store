import asyncio
import os
from tqdm import tqdm
from pathlib import Path
import shutil
import os
import sys

def get_dir_size(path):
    total_size = 0
    for file in path.rglob('*'):  # 遍历所有文件和子目录
        if file.is_file():
            total_size += file.stat().st_size
    return total_size

async def async_copy_file(src, dst, progress_bar):
    try:
        shutil.copy2(src, dst)  # 直接使用 shutil 复制文件
        progress_bar.update(os.path.getsize(src))  # 更新进度条
    except Exception as e:
        print(f"Error copying {src} to {dst}: {e}")

async def copy_directory(src, dst, force=False):
    tasks = []
    src_path = Path(src)
    dst_path = Path(dst)
    total_size = get_dir_size(src_path)
    progress_bar = tqdm(total=total_size, unit='B', unit_scale=True, desc="Copying files")

    for src_file in src_path.rglob('*'):  
        if src_file.is_file():
            dst_file = dst_path / src_file.relative_to(src_path)  # 计算目标路径
            if dst_file.exists() and not force:
                print(f"File {dst_file} already exists, pass -f to overwrite, skipping.")
                continue
            dst_file.parent.mkdir(parents=True, exist_ok=True)  # 确保目标目录存在
            tasks.append(async_copy_file(src_file, dst_file, progress_bar))
    
    await asyncio.gather(*tasks)
    progress_bar.close()

async def main():
    src, dst, force_ori = sys.argv[1], sys.argv[2], sys.argv[3]
    force = True if int(force_ori) == 1 else False
    await copy_directory(src, dst, force=force)

if __name__ == "__main__":
    asyncio.run(main())
