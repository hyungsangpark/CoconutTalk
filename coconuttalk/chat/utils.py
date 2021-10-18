import socket
import pickle
import struct

# Custom type used to denote client, format is as follows:
# ((ip_addresss, port), name, connected_time)
import time

Address = tuple[str, int]
Client = tuple[Address, str, float]
SERVER_HOST = "localhost"


def send(channel: socket.socket, *args) -> None:
    """
    Sends an object through the socket provided.
    :param channel: Socket to send the data
    :param args: Arguments in tuple.
    """
    buffer: bytes = pickle.dumps(args)
    value: int = socket.htonl(len(buffer))
    size: bytes = struct.pack("L", value)
    channel.send(size)
    channel.send(buffer)


def receive(channel: socket.socket) -> tuple:
    """
    Receives an object through the socket provided.

    Note that since the receiving object can be of any form of tuple, usage of this should be highly monitored.
    If there was an error in receiving data, an empty tuple will be returned.

    :param channel: Socket to receive the data.
    :return: A tuple of objects received from the socket. If there were error in receiving data, empty tuple; ().
    """
    size = struct.calcsize("L")
    size = channel.recv(size)
    try:
        size = socket.ntohl(struct.unpack("L", size)[0])
    except struct.error:
        return ()
    buf = ""
    while len(buf) < size:
        buf = channel.recv(size - len(buf))
    return pickle.loads(buf)


# def send_clients(channel, list_clients):
#     buffer = pickle.dumps(list(list_clients))
#     value = socket.htonl(len(buffer))
#     size = struct.pack("L", value)
#     channel.send(size)
#     channel.send(buffer)


# def receive_clients(channel):
#     size = struct.calcsize("L")
#     size = channel.recv(size)
#     try:
#         size = socket.ntohl(struct.unpack("L", size)[0])
#     except struct.error as e:
#         return ''
#     buf = ""
#     while len(buf) < size:
#         buf = channel.recv(size - len(buf))
#     return pickle.loads(buf)


def format_message(nickname: str, message: str) -> str:
    return f'{nickname} ({time.strftime("%H:%M", time.localtime())}): {message}'
