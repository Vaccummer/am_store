import paramiko
import os
import re
def parse_ssh_config(file_path):
    # 用于存储每个 host 的配置
    hosts = {}
    with open(file_path, 'r') as file:
        current_host = None
        host_config = {}

        for line in file:
            line = line.strip()

            if not line or line.startswith('#'):
                continue

            if line.lower().startswith('host '):
                if current_host:
                    hosts[current_host] = host_config
                current_host = line.split()[1]
                host_config = {}
                continue

            match = re.match(r'(\w+)\s+(.+)', line)
            if match:
                key, value = match.groups()
                host_config[key] = value
        if current_host:
            hosts[current_host] = host_config

    return hosts

class SshManager(object):
    def __init__(self):
        self.config_path = r'C:\Users\am\.ssh\config'
        self.server=None
        self._read_ssh_config()
    def _read_ssh_config(self):
        self.hosts = parse_ssh_config(self.config_path)
        self.hostnames = list(self.hosts.keys())
    def connect(self, host_name:str):
        assert host_name in self.hosts.keys(), f"Host name {host_name} not found in config file"
        host = self.hosts[host_name]
        self.server = paramiko.SSHClient()
        self.server.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.server.connect(host['HostName'], 
                            port=int(host.get('Port', 22)), 
                            username=host.get('User', os.getlogin()), 
                            password=host.get('Password', None))
            
        except Exception as e:
            return e
ssh = SshManager()
#print(ssh.hosts)
print(ssh.connect('bmc'))