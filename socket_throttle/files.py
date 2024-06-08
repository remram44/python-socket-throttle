from .core import Unlimited
from .leaky_bucket import LeakyBucket


class FileWrapper(object):
    def __init__(self, file, write=None, read=None):
        self._write_bucket = self._read_bucket = Unlimited()
        if write:
            if isinstance(write, (int, float)):
                send = LeakyBucket(write, write * 0.5)
            self._write_bucket = write
        if read:
            if isinstance(read, (int, float)):
                recv = LeakyBucket(read, read * 0.5)
            self._read_bucket = read

        self._file = file

    def __enter__(self):
        self._file.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self._file.__exit(exc_type, exc_val, exc_tb)

    def __next__(self):
        self._read_bucket.make_empty()
        ret = self._file.__next__()
        self._read_bucket.add_unchecked(ret)
        return ret

    close = lambda self: self._file.close
    closed = property(lambda self: self._file.closed)
    encoding = property(lambda self: self._file.encoding)
    fileno = lambda self: self._file.fileno
    flush = lambda self: self._file.flush
    isatty = lambda self: self._file.isatty
    mode = property(lambda self: self._file.mode)
    name = property(lambda self: self._file.name)
    readable = lambda self: self._file.readable
    seekable = lambda self: self._file.seekable
    tell = lambda self: self._file.tell
    writable = lambda self: self._file.writable

    def read(self, size=-1, /):
        if size > 0:
            self._read_bucket.make_available(size)
        else:
            self._read_bucket.make_empty()
        ret = self._file.read(size)
        self._read_bucket.add_unchecked(len(ret))
        return ret

    def seek(self, cookie, whence=0, /):
        return self._file.seek(cookie, whence)

    def truncate(self, pos=None, /):
        return self._file.truncate(pos)

    def write(self, buf, /):
        self._write_bucket.make_available(len(buf))
        ret = self._file.write(buf)
        self._write_bucket.add_unchecked(ret)
        return ret
