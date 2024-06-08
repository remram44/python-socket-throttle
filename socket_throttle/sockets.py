from .core import Unlimited
from .leaky_bucket import LeakyBucket


class SocketWrapper(object):
    def __init__(self, sock, send_bucket, recv_bucket):
        self._sock = sock
        self._send_bucket = send_bucket
        self._recv_bucket = recv_bucket

    @classmethod
    def limits(cls, sock, send_limit=None, recv_limit=None):
        send = recv = Unlimited()
        if send_limit:
            send = LeakyBucket(send_limit, send_limit * 0.1)
        if recv_limit:
            recv = LeakyBucket(recv_limit, recv_limit * 0.1)
        return cls(sock, send, recv)

    def close(self):
        self._sock.close()

    @property
    def family(self):
        return self._sock.family

    def fileno(self):
        return self._sock.fileno()

    def getpeername(self):
        return self._sock.getpeername()

    def getsockname(self):
        return self._sock.getsockname()

    def gettimeout(self):
        return self._sock.gettimeout()

    def settimeout(self, value):
        self._sock.settimeout(value)

    timeout = property(gettimeout)

    def getblocking(self):
        return self._sock.setblocking()

    def setblocking(self, flag):
        self._sock.setblocking(flag)

    def shutdown(self, how):
        self._sock.shutdown(how)

    def recv(self, bufsize, flags=0):
        self._recv_bucket.make_available(bufsize)
        data = self._sock.recv(bufsize, flags)
        self._recv_bucket.add_some(len(data))
        return data

    def recvfrom(self, bufsize, flags=0):
        self._recv_bucket.make_available(bufsize)
        data, address = self._sock.recvfrom(bufsize, flags)
        self._recv_bucket.add_some(len(data))
        return data, address

    def recvfrom_into(self, buffer, nbytes=0, flags=0):
        if not nbytes:
            nbytes = len(buffer)
        self._recv_bucket.make_available(nbytes)
        nbytes, address = self._sock.recvfrom_into(buffer, nbytes, flags)
        self._recv_bucket.add_some(nbytes)
        return nbytes, address

    def recv_into(self, buffer, nbytes=0, flags=0):
        if not nbytes:
            nbytes = len(buffer)
        self._recv_bucket.make_available(nbytes)
        nbytes = self._sock.recv_into(buffer, nbytes, flags)
        self._recv_bucket.add_some(nbytes)
        return nbytes

    def recvmsg(self, bufsize, ancbufsize=0, flags=0):
        self._recv_bucket.make_available(bufsize)
        data, ancdata, msg_flags, address = self._sock.recvmsg(
            bufsize,
            ancbufsize,
            flags,
        )
        self._recv_bucket.add_some(len(data))
        return data, ancdata, msg_flags, address

    def recvmsg_into(self, buffers, ancbufsize=0, flags=0):
        self._recv_bucket.make_available(self._recv_bucket.make_empty())
        nbytes, ancdata, msg_flags, address = self._sock.recvmsg_into(
            buffers,
            ancbufsize,
            flags,
        )
        self._recv_bucket.add_some(nbytes)
        return nbytes, ancdata, msg_flags, address

    def send(self, bytes, flags=0):
        self._send_bucket.make_available(len(bytes))
        nbytes = self._sock.send(bytes, flags)
        self._send_bucket.add_some(nbytes)
        return nbytes

    def sendall(self, bytes, flags=0):
        self._send_bucket.add_some(len(bytes))
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
        self._send_bucket.add_some(nbytes)
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
        self._send_bucket.add_some(nbytes)
        return nbytes
