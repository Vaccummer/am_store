import shutil
import os
from typing import Callable
import asyncio
shutil.copytree()

class LocalTransfer:
    def __init__(self, thread_num:int=4, chunk_size:int=1024*1024*4):
        super().__init__()
        self.thread_num = thread_num
        self.chunk_size = chunk_size
        self.callback = None
    
    def transfer(self, task_f:list[tuple[str, str]]):
        asyncio.run(self._transfer(task_f))
        self.callback = None
    
    async def _transfer(self, task_f):
        for i in range(0,len(task_f),self.thread_num):
            task_f_i = task_f[i:i+self.thread_num]
            task_l = []
            for task_i in task_f_i:
                task_l.append(self.copy_with_progress(task_i[0], task_i[1], os.path.getsize(task_i[0])))
            await asyncio.gather(*task_l)

    async def copy_with_progress(self, src, dst, total_size):
        copied_size = 0

        with open(src, "rb") as fsrc, open(dst, "wb") as fdst:
            while chunk := fsrc.read(int(self.chunk_size)):  
                fdst.write(chunk)
                copied_size += len(chunk)
                if self.callback:
                    self.callback(src, dst, copied_size, total_size)

if __name__ == '__main__':
    path_l = 
