import select
import sys

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

            # Send my name...
            send(self.sock, 'NAME: ' + self.nickname)
            data = receive(self.sock)

            # Contains client address, set it
            print("received address data: " + data)
            self.connected_address, connected_port_str = data.split('CLIENT: ')[1].split(":")
            self.connected_port = int(connected_port_str)
            self.prompt = '[' + '@'.join((self.nickname, self.connected_address)) + ']> '
        except socket.error:
            print(f'Failed to connect to chat server @ port {self.server_port}')
            raise socket.error

    def get_all_clients(self) -> list[Client]:
        """
        Retrieves list of clients currently connected to the server.
        :return: A tuple with list of client information
        """
        send(self.sock, "GET_ALL_CLIENTS")
        return receive_clients(self.sock)

    def cleanup(self):
        """
        Close the connection and wait for the thread to terminate.
        :return:
        """
        self.sock.close()

    def fetch_messages(self) -> list[str]:
        messages: list[str] = []

        # Wait for input from stdin and socket
        readable, writeable, exceptional = select.select([self.sock], [], [])

        for sock in readable:
            data = receive(sock)
            if not data:
                client_port, _, message = data.partition(":")
                print(f'Client: {client_port} shutting down.')
                messages.append(f'SHUTDOWN:{client_port}')
            else:
                messages.append(data)

        return messages

    # def run(self):
    #     """
    #     Chat client main loop
    #     :return:
    #     """
    #     while self.connected:
    #         try:
    #             sys.stdout.write(self.prompt)
    #             sys.stdout.flush()
    #
    #             # Wait for input from stdin and socket
    #             readable, writeable, exceptional = select.select(
    #                 [0, self.sock], [], [])
    #
    #             for sock in readable:
    #                 if sock == 0:
    #                     data = sys.stdin.readline().strip()
    #                     if data == "GET_ALL_CLIENTS":
    #                         send(self.sock, data)
    #                         print(f"{self.prompt}{receive_clients(self.sock)}")
    #                     elif data:
    #                         send(self.sock, data)
    #                 elif sock == self.sock:
    #                     data = receive(self.sock)
    #                     if not data:
    #                         print('Client shutting down.')
    #                         self.connected = False
    #                         break
    #                     else:
    #                         sys.stdout.write(data + '\n')
    #                         sys.stdout.flush()
    #
    #         except KeyboardInterrupt:
    #             print(" Client interrupted. """)
    #             self.cleanup()
    #             break
