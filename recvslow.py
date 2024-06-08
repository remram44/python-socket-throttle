import socket
from socket_throttle.sockets import SocketWrapper
import sys


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
sock.connect(('127.0.0.1', 5000))

sock = SocketWrapper(sock, 100, 100)

while True:
    data = sock.recv(20)
    sys.stdout.buffer.write(data)
