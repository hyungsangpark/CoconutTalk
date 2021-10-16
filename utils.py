import socket
import pickle
import struct


def send(channel: socket.socket, *args) -> None:
    """

    :param channel:
    :param args:
    :return:
    """
    buffer: bytes = pickle.dumps(args)
    value: int = socket.htonl(len(buffer))
    size: bytes = struct.pack("L", value)
    channel.send(size)
    channel.send(buffer)


def receive(channel: socket.socket) -> str:
    """

    :param channel:
    :return:
    """
    size = struct.calcsize("L")
    size = channel.recv(size)
    try:
        size = socket.ntohl(struct.unpack("L", size)[0])
    except struct.error:
        return ''
    buf = ""
    while len(buf) < size:
        buf = channel.recv(size - len(buf))
    return pickle.loads(buf)[0]


def send_clients(channel, list_clients):
    buffer = pickle.dumps(list(list_clients))
    value = socket.htonl(len(buffer))
    size = struct.pack("L", value)
    channel.send(size)
    channel.send(buffer)


def receive_clients(channel):
    size = struct.calcsize("L")
    size = channel.recv(size)
    try:
        size = socket.ntohl(struct.unpack("L", size)[0])
    except struct.error as e:
        return ''
    buf = ""
    while len(buf) < size:
        buf = channel.recv(size - len(buf))
    return pickle.loads(buf)

