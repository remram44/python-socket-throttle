from socket_throttle import LeakyBucket
from socket_throttle.files import FileWrapper
import sys


file_input = sys.stdin.buffer
file_output = sys.stdout.buffer

if sys.argv[1] == 'input':
    file_input = FileWrapper(
        file_input,
        read=LeakyBucket(int(sys.argv[2]), int(sys.argv[3])),
    )
elif sys.argv[1] == 'output':
    file_output = FileWrapper(
        file_output,
        write=LeakyBucket(int(sys.argv[2]), int(sys.argv[3])),
    )
else:
    raise ValueError("invalid argument")

while True:
    data = file_input.read(8192)
    file_output.write(data)
