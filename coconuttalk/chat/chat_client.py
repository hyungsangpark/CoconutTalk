import select

from coconuttalk.chat.utils import *


class ChatClient:
    """
    A command line chat client using select
    """

    def __init__(self, nickname, port, host=SERVER_HOST):
        self.nickname = nickname
        self.connected = False
        self.server_address: str = host
        self.server_port: int = port
        # Default (invalid) values for connected address and port.
        self.connected_address: str = ""
        self.connected_port: int = -1

        # Initial prompt
        self.prompt = f'[{nickname}@{socket.gethostname()}]> '

        # Connect to server at port
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((host, self.server_port))
            print(f'Now connected to chat server@ port {self.server_port}')
            self.connected = True

            # Send my name.
            # Convention: ("NAME", "hyung")
            send(self.sock, "NAME", self.nickname)

            # Receive client address.
            # Convention: ("CLIENT", ('127.0.0.1', 15151))
            self.connected_address, self.connected_port = receive(self.sock)[1]

            # Contains client address, set it
            # print("received address data: " + data)
            # self.connected_address, connected_port_str = data.split('CLIENT: ')[1].split(":")
            # self.connected_port = int(connected_port_str)
            # self.prompt = '[' + '@'.join((self.nickname, self.connected_address)) + ']> '
        except socket.error:
            print(f'Failed to connect to chat server @ port {self.server_port}')
            raise socket.error

    def get_all_clients(self) -> list[Client]:
        """
        Retrieves list of clients currently connected to the server.
        :return: A tuple with list of client information
        """
        send(self.sock, "GET_ALL_CLIENTS")
        # description, clients = receive(self.sock)
        return receive(self.sock)[1]

    def cleanup(self):
        """
        Close the connection and wait for the thread to terminate.
        :return:
        """
        self.sock.close()

    def leave_room(self, room_name: str) -> None:
        send(self.sock, "EXITROOM", room_name)

    def fetch_messages(self) -> list[str]:
        messages: list[str] = []

        # Wait for input from stdin and socket
        readable, writeable, exceptional = select.select([self.sock], [], [])

        for sock in readable:
            data = receive(sock)[0]
            print(data)
            if data == "EXITROOM_OK":
                # last message from the server.
                print("Room left.")
            else:
                messages.append(data)

        return messages

    def send_message(self, room_name: str, message: str) -> None:
        send(self.sock, "MESSAGE", room_name, message)
