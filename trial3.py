import asyncio
import asyncssh
import os

async def transfer_large_file_sftp(local_file, remote_path, remote_host, remote_user, remote_password):
    try:
        async with asyncssh.connect(remote_host, username=remote_user, password=remote_password) as conn:
            async with conn.start_sftp_client() as sftp:
                file_size = os.path.getsize(local_file)
                def progress(src:str, dst:str, current:int, total:int):
                    print(f"{current}/{total} bytes ({(current / total) * 100:.2f}%)")
                    #print(f"上传进度：{current}/{total} bytes ({(current / total) * 100:.2f}%)")
                await sftp.put(local_file, remote_path, block_size=1024*1024*8, progress_handler=progress)
    except Exception as e:
        print(f"文件传输失败: {e}")

local_file = r"F:\Windows_Data\Desktop_File\mp3.zip"   
remote_path = r"C:\Users\am"  
remote_host = "192.168.31.46"            
remote_user = "am"           
remote_password = "1984" 

import time
a = time.time()
asyncio.run(transfer_large_file_sftp(local_file, remote_path, remote_host, remote_user, remote_password))
b = time.time()
print(b-a)