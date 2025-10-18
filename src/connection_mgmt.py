import binascii
import json
import os
import subprocess
from threading import Thread

from protocols import Protocol, UnknownProtocolException


CONNECTION_FILE = "connections.json"
if not os.path.exists(CONNECTION_FILE):
    with open(CONNECTION_FILE, 'w') as f:
        json.dump([], f)


class Connection:

    def __init__(self, name, protocol: Protocol, address, username, salt):

        self.name = name
        self.protocol = protocol

        if protocol not in [*Protocol]:
            raise UnknownProtocolException(f"Protocol {protocol} unknown")
        
        self.address = address
        self.username = username
        self.salt = salt

    def connect(self):
        match self.protocol:

            case Protocol.VNC:
                command = [r'C:\Program Files\uvnc bvba\UltraVNC\vncviewer.exe']
                raise NotImplemented("Need to research and test connection")
            
            case Protocol.SSH:
                command = " ".join(['start', r'C:\Windows\System32\OpenSSH\ssh.exe', f'{self.username}@{self.address}'])
                thread = Thread(target=os.system, args=([command,]))
                thread.start()

            case Protocol.RDP:
                command = " ".join(["cmdkey", f'/generic:"{self.address}"', f'/user:"{self.username}"'])
                subprocess.run(command)
                command = " ".join([r"C:\WINDOWS\system32\mstsc.exe", "/v:{address}"])
                subprocess.run(command)
                command = " ".join(["cmdkey", "/delete:{self.address}"])
                subprocess.run(command)

            case Protocol.FTP:                
                command = [r"C:\Program Files\FileZilla FTP Client\filezilla.exe", f"ftp://{self.username}@{self.address}"]
                subprocess.run(" ".join(command))

    def to_json(self):
        return {
            "name": self.name,
            "protocol": self.protocol.name,
            "address": self.address,
            "username": self.username,
            "salt": binascii.hexlify(self.salt).decode()
        }

    @staticmethod
    def load_connections(password_manager):
        password = password_manager.get_password()
        with open(CONNECTION_FILE, 'r') as f:
            serialized_connections = json.loads(f.read())
        connections = [
            Connection(
                name=c['name'],
                protocol=[p for p in Protocol if c['protocol'] == p.name][0],
                address=password_manager.decrypt_data(password, c['salt'], c['address']),
                username=password_manager.decrypt_data(password, c['salt'], c['username']),
                salt=binascii.unhexlify(c['salt'])
            )
            for c in serialized_connections
        ]
        return connections

    @staticmethod
    def add_connection(password_manager, connection):
        connections = Connection.load_connections(password_manager)
        connections = [x for x in Connection.load_connections(password_manager)]
        connections.append(connection)
        password = password_manager.get_password()
        for c in connections:
            c.address = password_manager.encrypt_data(password, c.salt, c.address)
            c.username = password_manager.encrypt_data(password, c.salt, c.username)
        with open(CONNECTION_FILE, 'w') as f:
            json.dump(connections, f)

    @staticmethod
    def remove_connection(password_manager, pruned_connection_name):
        if pruned_connection_name:
            connections = [x for x in Connection.load_connections(password_manager) if x.name != pruned_connection_name]
            password = password_manager.get_password()
            for c in connections:
                c.address = password_manager.encrypt_data(password, c.salt, c.address)
                c.username = password_manager.encrypt_data(password, c.salt, c.username)
            with open(CONNECTION_FILE, 'w') as f:
                json.dump(connections, f)


def _default(self, obj):
    return getattr(obj.__class__, "to_json", _default.default)(obj)


_default.default = json.JSONEncoder().default
json.JSONEncoder.default = _default
