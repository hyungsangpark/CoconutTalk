import select
import signal
import sys
import time

from coconuttalk.chat.utils import *


class ChatServer:
    """ An example chat server using select """

    def __init__(self, port, backlog=5):
        self.clients = 0
        self.client_map: dict[socket.socket, Client] = {}
        self.rooms: dict[str, list[socket.socket]] = {}
        self.outputs = []  # list output sockets
        self.server_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((SERVER_HOST, port))
        self.server_socket.listen(backlog)
        # Catch keyboard interrupts
        signal.signal(signal.SIGINT, self.sighandler)

        print(f'Server listening to port: {port} ...')

    def sighandler(self, signum, frame):
        """ Clean up client outputs"""
        print('Shutting down server...')

        # Close existing client sockets
        for output in self.outputs:
            output.close()

        self.server_socket.close()

    def get_client_name(self, client):
        """ Return the name of the client """
        info = self.client_map[client]
        host, name = info[0][0], info[1]
        return '@'.join((name, host))

    def get_client_socket(self, port_num: int) -> socket.socket:
        f"""
        Given a port number of a client, it returns the socket instance of the client.

        :param port_num: Port of the client socket to find.
        :return: socket instance of the client with the given port.
        """
        for client_socket, client_info in self.client_map.items():
            if client_info[0][1] == port_num:
                return client_socket

    def run(self):
        inputs = [self.server_socket, sys.stdin]
        self.outputs = []
        running = True
        while running:
            try:
                readable, writeable, exceptional = select.select(
                    inputs, self.outputs, [])
            except select.error as e:
                break

            for sock in readable:
                sys.stdout.flush()
                if sock == self.server_socket:
                    # handle the server socket
                    client, address = self.server_socket.accept()
                    print(
                        f'Chat server: got connection {client.fileno()} from {address}')
                    # Read the login name
                    cname = receive(client).split('NAME: ')[1]

                    # Compute client name and send back
                    self.clients += 1
                    send(client, f'CLIENT: {str(address[0])}:{str(address[1])}')
                    inputs.append(client)

                    self.client_map[client] = (address, cname, time.time())
                    # Send joining information to other clients
                    msg = f'\n(Connected: New client ({self.clients}) from {self.get_client_name(client)})'
                    for output in self.outputs:
                        send(output, msg)
                    self.outputs.append(client)

                elif sock == sys.stdin:
                    # didn't test sys.stdin on windows system
                    # handle standard input
                    cmd = sys.stdin.readline().strip()
                    if cmd == 'list':
                        print(self.client_map.values())
                    elif cmd == 'quit':
                        running = False
                else:
                    # handle all other sockets
                    try:
                        data = receive(sock)
                        print("data: " + data)
                        if data == "GET_ALL_CLIENTS":
                            send_clients(sock, self.client_map.values())

                        elif data.startswith("CREATEROOM:"):
                            _, room_name, chatting_client_port = data.split(":")
                            message = ""
                            try:
                                _ = self.rooms[room_name]
                                message = "Room with given name already exists. Please try a different name."
                            except KeyError:
                                self.rooms[room_name] = [sock]
                                if chatting_client_port != "null":
                                    self.rooms[room_name].append(self.get_client_socket(int(chatting_client_port)))
                                message = "SUCCESS"
                            finally:
                                print(message + f"\nRoom: {room_name} has been created.")
                                send(sock, message)

                        elif data.startswith("CLOSEROOM:"):
                            _, room_name = data.split(":")
                            try:
                                self.rooms.pop(room_name)
                            except KeyError as e:
                                print(f"Room: {room_name} does not exist.")
                                _ = e
                            print(f"Room: {room_name} has been deleted.")

                        elif data:
                            # Send as new client's message...
                            msg = f'\n#[{self.get_client_name(sock)}]>> {data}'

                            # Send data to all except ourself
                            for output in self.outputs:
                                if output != sock:
                                    send(output, msg)
                        else:
                            print(f'Chat server: {sock.fileno()} hung up')
                            self.clients -= 1
                            sock.close()
                            inputs.remove(sock)
                            self.outputs.remove(sock)

                            # Sending client leaving information to others
                            msg = f'\n(Now hung up: Client from {self.get_client_name(sock)})'
                            self.client_map.pop(sock)

                            for output in self.outputs:
                                send(output, msg)
                    except socket.error:
                        # Remove
                        inputs.remove(sock)
                        self.outputs.remove(sock)

        self.server_socket.close()
