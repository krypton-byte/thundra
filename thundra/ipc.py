import struct
import socket
from logging import getLogger, DEBUG, NOTSET
from typing import Callable, Dict

log = getLogger()


class Leo:
    def __init__(self) -> None:
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.sock.connect("listen.sock")
        self.handler: Dict[str, Callable[[bytes]]] = {}

    def default_handler(self, arg: str):
        print(arg)

    def on_message(self, command: str, data: bytes):
        f = self.handler.get(command)
        if f:
            f(data)
        else:
            log.debug(f"{command} command not set on current handler")

    def set_handler(self, command: str, f: Callable[[bytes], None]):
        self.handler.update({command: f})

    def get_data(self):
        while True:
            command_size = self.sock.recv(4)
            command = self.sock.recv(struct.unpack("i", command_size)[0])
            data_size = self.sock.recv(4)
            data = self.sock.recv(struct.unpack("i", data_size)[0])
            self.on_message(command.decode(), data)

    def send_commmand(self, name: str, message: bytes = b"notset"):
        self.sock.send(struct.pack("i", len(name)))
        self.sock.send(name.encode())
        self.sock.send(struct.pack("i", len(message)))
        self.sock.send(message)


lexz = Leo()
