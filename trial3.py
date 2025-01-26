from genericpath import isfile
import asyncssh
from am_store.common_tools import *
import os
import asyncio
import time
from glob import glob


def progress_handler(src:str, dst:str, sent:int, total_size:int):
    if total_size >0:
        print(f"{sent/total_size*100:.2f}%")

async def transfer_file(src:str, dst:str):
    async with asyncssh.connect("172.26.36.83", 
                            username='am', 
                            password='1984',
                            port=22) as conn:
        async with conn.start_sftp_client() as sftp_f:
            await sftp_f.put(src,dst,max_requests=2,recurse=True)

if __name__ == '__main__':
    for i in glob(r'D:\Document\Desktop\output_archive\lib\**', recursive=True):
        if os.path.isfile(i):
            print(i)
        elif (not os.listdir(i)):
            print(i)
            
    os._exit(0)
    src = r'D:\Downloads\so_down\CAD2023\hello.zip'
    dst = r'/home/am/tm'
    start_t = time.time()
    try:
        asyncio.run(transfer_file(src, dst))
    except Exception as e:
        print(type(e))
        os._exit(0)
    end_t = time.time()
    size_f = os.path.getsize(src)/1024/1024
    print(f'time: {end_t-start_t:.2f}s')
    print(f'size: {size_f:.2f}MB')
    print(f'speed: {size_f/(end_t-start_t):.2f}MB/s')

