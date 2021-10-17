import select
import sys

from coconuttalk.chat.chat_utils import *


class ChatClient:
    """
    A command line chat client using select
    """

    def __init__(self, name, port, host=SERVER_HOST):
        self.name = name
        self.connected = False
        self.host = host
        self.port = port

        # Initial prompt
        self.prompt = f'[{name}@{socket.gethostname()}]> '

        # Connect to server at port
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((host, self.port))
            print(f'Now connected to chat server@ port {self.port}')
            self.connected = True

            # Send my name...
            send(self.sock, 'NAME: ' + self.name)
            data = receive(self.sock)

            # Contains client address, set it
            addr = data.split('CLIENT: ')[1]
            self.prompt = '[' + '@'.join((self.name, addr)) + ']> '
        except socket.error:
            print(f'Failed to connect to chat server @ port {self.port}')
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

    def run(self):
        """
        Chat client main loop
        :return:
        """
        while self.connected:
            try:
                sys.stdout.write(self.prompt)
                sys.stdout.flush()

                # Wait for input from stdin and socket
                readable, writeable, exceptional = select.select(
                    [0, self.sock], [], [])

                for sock in readable:
                    if sock == 0:
                        data = sys.stdin.readline().strip()
                        if data == "GET_ALL_CLIENTS":
                            send(self.sock, data)
                            print(f"{self.prompt}{receive_clients(self.sock)}")
                        elif data:
                            send(self.sock, data)
                    elif sock == self.sock:
                        data = receive(self.sock)
                        if not data:
                            print('Client shutting down.')
                            self.connected = False
                            break
                        else:
                            sys.stdout.write(data + '\n')
                            sys.stdout.flush()

            except KeyboardInterrupt:
                print(" Client interrupted. """)
                self.cleanup()
                break
