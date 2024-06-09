from .core import Unlimited
from .leaky_bucket import LeakyBucket


class SocketWrapper(object):
    def __init__(self, sock, send=None, recv=None):
        self._send_bucket = self._recv_bucket = Unlimited()
        if send:
            if isinstance(send, (int, float)):
                send = LeakyBucket(send, send * 0.5)
            self._send_bucket = send
        if recv:
            if isinstance(recv, (int, float)):
                recv = LeakyBucket(recv, recv * 0.5)
            self._recv_bucket = recv

        self._sock = sock

    close = lambda self: self._sock.close()
    _closed = property(lambda self: self._sock._closed())
    family = property(lambda self: self._sock.family())
    fileno = lambda self: self._sock.fileno()
    getpeername = lambda self: self._sock.getpeername()
    getsockname = lambda self: self._sock.getsockname()
    gettimeout = lambda self: self._sock.gettimeout()
    timeout = property(gettimeout)
    getblocking = lambda self: self._sock.getblocking()

    def settimeout(self, value):
        self._sock.settimeout(value)

    def setblocking(self, flag):
        self._sock.setblocking(flag)

    def shutdown(self, how):
        self._sock.shutdown(how)

    def recv(self, bufsize, flags=0):
        self._recv_bucket.make_available(bufsize)
        data = self._sock.recv(bufsize, flags)
        self._recv_bucket.add_unchecked(len(data))
        return data

    def recvfrom(self, bufsize, flags=0):
        self._recv_bucket.make_available(bufsize)
        data, address = self._sock.recvfrom(bufsize, flags)
        self._recv_bucket.add_unchecked(len(data))
        return data, address

    def recvfrom_into(self, buffer, nbytes=0, flags=0):
        if not nbytes:
            nbytes = len(buffer)
        self._recv_bucket.make_available(nbytes)
        nbytes, address = self._sock.recvfrom_into(buffer, nbytes, flags)
        self._recv_bucket.add_unchecked(nbytes)
        return nbytes, address

    def recv_into(self, buffer, nbytes=0, flags=0):
        if not nbytes:
            nbytes = len(buffer)
        self._recv_bucket.make_available(nbytes)
        nbytes = self._sock.recv_into(buffer, nbytes, flags)
        self._recv_bucket.add_unchecked(nbytes)
        return nbytes

    def recvmsg(self, bufsize, ancbufsize=0, flags=0):
        self._recv_bucket.make_available(bufsize)
        data, ancdata, msg_flags, address = self._sock.recvmsg(
            bufsize,
            ancbufsize,
            flags,
        )
        self._recv_bucket.add_unchecked(len(data))
        return data, ancdata, msg_flags, address

    def recvmsg_into(self, buffers, ancbufsize=0, flags=0):
        self._recv_bucket.make_available(self._recv_bucket.make_empty())
        nbytes, ancdata, msg_flags, address = self._sock.recvmsg_into(
            buffers,
            ancbufsize,
            flags,
        )
        self._recv_bucket.add_unchecked(nbytes)
        return nbytes, ancdata, msg_flags, address

    def send(self, bytes, flags=0):
        self._send_bucket.make_available(len(bytes))
        nbytes = self._sock.send(bytes, flags)
        self._send_bucket.add_unchecked(nbytes)
        return nbytes

    def sendall(self, bytes, flags=0):
        self._send_bucket.add_unchecked(len(bytes))
        self._sock.sendall(bytes, flags)

    def sendfile(self, file, offset=0, count=None):
        if offset:
            file.seek(offset)
        blocksize = min(count, 8192) if count else 8192
        total_sent = 0
        file_read = file.read
        try:
            while True:
                if count:
                    blocksize = min(count - total_sent, blocksize)
                    if blocksize <= 0:
                        break
                data = memoryview(file_read(blocksize))
                if not data:
                    break  # EOF
                while True:
                    try:
                        sent = self.send(data)
                    except BlockingIOError:
                        continue
                    else:
                        total_sent += sent
                        if sent < len(data):
                            data = data[sent:]
                        else:
                            break
            return total_sent
        finally:
            if total_sent > 0 and hasattr(file, 'seek'):
                file.seek(offset + total_sent)

    def sendmsg(self, buffers, ancdata=None, flags=0, address=None):
        self._send_bucket.make_empty()
        nbytes = self._sock.sendmsg(buffers, ancdata, flags, address)
        self._send_bucket.add_unchecked(nbytes)
        return nbytes

    def sendto(self, *args):
        if len(args) == 2:
            bytes, address = args
            flags = 0
        elif len(args) == 3:
            bytes, flags, address = args
        else:
            raise TypeError("invalid arguments")

        self._send_bucket.make_available(len(bytes))
        nbytes = self._sock.sendto(bytes, address, flags)
        self._send_bucket.add_unchecked(nbytes)
        return nbytes
