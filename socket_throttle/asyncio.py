class StreamReaderWrapper(object):
    def __init__(self, reader, bucket):
        self._reader = reader
        self._bucket = bucket

    async def read(self, n=-1):
        if n == 0:
            n = 65536
        n = await self._bucket.async_make_available(1, n)
        ret = await self._reader.read(n)
        self._bucket.add_unchecked(len(ret))
        return ret

    async def readline(self):
        await self._bucket.async_make_empty()
        ret = await self._reader.readline()
        self._bucket.add_unchecked(len(ret))
        return ret

    async def readexactly(self, n):
        assert n > 0
        await self._bucket.async_make_available(n)
        ret = await self._reader.readexactly(n)
        self._bucket.add_unchecked(len(ret))
        return ret

    async def readuntil(self, separator=b'\n'):
        await self._bucket.async_make_empty()
        ret = await self._reader.readuntil(separator)
        self._bucket.add_unchecked(len(ret))
        return ret

    at_eof = lambda self: self._reader.at_eof()


class StreamWriterWrapper(object):
    def __init__(self, writer, bucket):
        self._writer = writer
        self._bucket = bucket

    close = lambda self: self._writer.close()
    can_write_eof = lambda self: self._writer.can_write_eof()
    write_eof = lambda self: self._writer.write_eof()
    transport = property(lambda self: self._writer.transport)

    def get_extra_info(self, default=None):
        return self._writer.get_extra_info(default)

    def write(self, data):
        self._writer.write(data)

    def writelines(self, data):
        self._writer.writelines(data)

    async def drain(self):
        TODO
