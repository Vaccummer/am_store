import paramiko
import os

# 回调函数，用于显示进度
def progress_callback(filename, bytes_sent, total_size):
    progress = (bytes_sent / total_size) * 100
    print(f"传输进度 {filename}: {bytes_sent}/{total_size} bytes ({progress:.2f}%)")

# 使用 paramiko.Transport 传输大文件
def transfer_large_file_transport(local_path, remote_path, remote_host, remote_user, remote_password):
    # 创建一个Transport对象
    transport = paramiko.Transport((remote_host, 22))

    try:
        # 连接到远程服务器
        transport.connect(username=remote_user, password=remote_password)
        print(f"已连接到 {remote_host}")

        # 使用 Transport 对象创建 SFTP 会话
        sftp = paramiko.SFTPClient.from_transport(transport)

        # 获取本地文件大小
        local_size = os.path.getsize(local_path)
        
        # 打开远程文件进行写入（以二进制写入方式打开）
        with sftp.open(remote_path, 'wb') as remote_file:
            with open(local_path, 'rb') as local_file:
                buffer_size = int(1024*1024*512)  # 32KB
                bytes_sent = 0
                while chunk := local_file.read(buffer_size):
                    remote_file.write(chunk)
                    bytes_sent += len(chunk)
                    # 调用进度回调函数
                    progress_callback(local_path, bytes_sent, local_size)
        
        # 完成文件传输
        print(f"文件 {local_path} 成功上传到 {remote_path}")

        # 关闭 SFTP 客户端和 Transport 连接
        sftp.close()
        transport.close()
        
    except Exception as e:
        print(f"文件传输失败: {e}")

local_file = r"F:\Windows_Data\Desktop_File"   # 本地文件路径
remote_path = r"C:\Users\am"  # 远程文件路径
remote_host = "192.168.31.46"            # 远程服务器的IP地址
remote_user = "am"               # 远程服务器的用户名
remote_password = "1984"       # 远程服务器的密码
import time
a = time.time()
transfer_large_file_transport(local_file, remote_path, remote_host, remote_user, remote_password)
b = time.time()
print(b-a)

# # 使用示例
# local_file = r"F:\Windows_Data\Desktop_File\mp3.zip"   # 本地文件路径
# remote_path = "/home/am/mp4.zip"  # 远程文件路径
# remote_host = "localhost"            # 远程服务器的IP地址
# remote_user = "am"               # 远程服务器的用户名
# remote_password = "1984"       # 远程服务器的密码

# transfer_file_paramiko(local_file, remote_path, remote_host, remote_user, remote_password)

