# Socket throttling for Python

This tiny library contains a wrapper for sockets that can be used to limit their send and/or receive rate to a specific value.

It can be used to limit the bandwidth use of any Python code that uses sockets.

Example:

```python
import socket
from socket_throttle import LeakyBucket
from socket_throttle.sockets import SocketWrapper


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
sock.connect(('127.0.0.1', 5000))

# Short syntax, limit sending to 2kB/s and receiving to 100kB/s
sock = SocketWrapper(sock, send=2_000, recv=100_000)

# Longer syntax, create a bucket that can be shared by multiple sockets
# Receive speed is unlimited
send_bucket = LeakyBucket(100_000, 500_000)
sock = SocketWrapper(sock, send=send_bucket)

# It works with files too
from socket_throttle.files import FileWrapper

with open('data.bin', 'rb') as file:
    file = FileWrapper(file, read=100_000)
    file.read(...)
```
