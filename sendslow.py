import socket
from socket_throttle import SocketWrapper


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
sock.connect(('127.0.0.1', 5000))

sock = SocketWrapper.limits(sock, 100, 100)

buffer = b'1234567890' * 2

while True:
    sock.send(buffer)
