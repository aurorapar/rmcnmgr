from enum import Enum
import subprocess

class Protocol(Enum):
    VNC = 1,
    RDP = 2,
    SSH = 3,
    FTP = 4


PROTOCOL_PORTS = {
    Protocol.VNC: 5900,
    Protocol.RDP: 3389,
    Protocol.SSH: 22,
    Protocol.FTP: 5900,
}


class UnknownProtocolException(Exception):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
