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
        return self.client_map[client][1]

    def get_client_socket(self, port_num: int) -> socket.socket:
        """
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
            except select.error:
                break

            for sock in readable:
                sys.stdout.flush()
                if sock == self.server_socket:
                    # handle the server socket
                    client, address = self.server_socket.accept()
                    print(
                        f'Chat server: got connection {client.fileno()} from {address}')
                    # Read the login name
                    cname: str = receive(client)[1]

                    # Compute client name and send back
                    self.clients += 1
                    print(address)
                    send(client, "CLIENT", address)
                    # send(client, f'CLIENT: {str(address[0])}:{str(address[1])}')
                    inputs.append(client)

                    self.client_map[client] = (address, cname, time.time())
                    # Send joining information to other clients
                    # msg = f'\n(Connected: New client ({self.clients}) from {self.get_client_name(client)})'
                    # for output in self.outputs:
                    #     send(sock, "CLIENTLIST", *self.client_map.values())
                        # send(output, msg)
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
                    # handle all other messages into the server's socket.
                    try:
                        data = receive(sock)
                        print(f"data: {data}")

                        if data == ():
                            print(f'Chat server: {sock.fileno()} hung up')
                            self.clients -= 1
                            sock.close()
                            inputs.remove(sock)
                            self.outputs.remove(sock)

                            # Sending client leaving information to others
                            # msg = f'\n(Now hung up: Client from {self.get_client_name(sock)})\n'
                            self.client_map.pop(sock)

                            # this change will soon be detected by clients. No need to manually update again.
                            # for output in self.outputs:
                            #     send(output, msg)

                        elif data[0] == "GET_ALL_CLIENTS":
                            send(sock, *self.client_map.values())

                        # Convention: ("CREATEROOM", "room_name_hehe_xd", 13531)
                        elif data[0] == "CREATEROOM":
                            _, room_name, chatting_client_port = data
                            message = ""
                            return_code = ""
                            try:
                                _ = self.rooms[room_name]
                                message = "Room with given name already exists. Please try a different name."
                                return_code = "EXISTS"
                            except KeyError:
                                self.rooms[room_name] = [sock]
                                if chatting_client_port != -1:
                                    self.rooms[room_name].append(self.get_client_socket(chatting_client_port))
                                message = f"Room: {room_name} has been created."
                                return_code = "SUCCESS"
                            finally:
                                print(message)
                                send(sock, return_code)

                        elif data[0] == "JOINROOM":
                            _, room_name = data
                            return_code = ""

                            try:
                                self.rooms[room_name].append(sock)
                                return_code = "SUCCESS"
                            except KeyError:
                                return_code = "FAIL"
                            finally:
                                send(sock, return_code)

                        # Convention: ("CLOSEROOM", "room_name_hehe_xd")
                        elif data[0] == "EXITROOM":
                            # Change this.
                            _, room_name = data

                            try:
                                self.rooms[room_name].remove(sock)
                                if not self.rooms[room_name]:
                                    self.rooms.pop(room_name)
                            except KeyError:
                                print(f"Room: {room_name} does not exist.")

                            send(sock, "EXITROOM")
                            print(f"Room: {room_name} has been deleted.")

                        # Convention: ("MESSAGE", "Hello, World!")
                        elif data[0] == "MESSAGE":
                            # Send as new client's message...
                            # msg = f'{self.get_client_name(sock)}:{data}'
                            msg = format_message(self.get_client_name(sock), data[1])

                            # Send data to all except ourself
                            for output in self.outputs:
                                if output != sock:
                                    send(output, msg)

                        else:
                            print("Not sure what happened; Something strange happened in chat_server.py?")

                    except socket.error:
                        # Remove
                        inputs.remove(sock)
                        self.outputs.remove(sock)

        self.server_socket.close()
