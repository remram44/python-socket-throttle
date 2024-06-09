from paramiko import SSHClient
from scp import SCPClient
import socket
from socket_throttle.sockets import SocketWrapper
import sys


def connect(host, port):
    for info in socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP):
        af, socktype, proto, canonname, sa = info
        try:
            sock = socket.socket(af, socktype, proto)
        except OSError:
            continue
        try:
            sock.connect(sa)
        except OSError:
            sock.close()
            continue
        return sock
    print("Couldn't connect", file=sys.stderr)
    sys.exit(1)


def parse(string):
    host, path = string.split(':', 1)
    if '@' in host:
        username, host = host.split('@', 1)
    else:
        username = None
    return host, username, path


source, dest, limit = sys.argv[1:]
limit = int(limit, 10)


ssh = SSHClient()
ssh.load_system_host_keys()

if ':' in source and ':' not in dest:
    host, username, path = parse(source)
    sock = connect(host, 22)
    sock = SocketWrapper(sock, limit, limit)
    ssh.connect(host, username=username, sock=sock)

    scp = SCPClient(ssh.get_transport())
    scp.get(path, dest)
elif ':' in dest and ':' not in source:
    host, username, path = parse(dest)
    sock = connect(host, 22)
    sock = SocketWrapper(sock, limit, limit)
    ssh.connect(host, username=username, sock=sock)

    scp = SCPClient(ssh.get_transport())
    scp.put(source, path)
