import select
import signal
import ssl
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

        self.context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        self.context.load_cert_chain(certfile="cert.pem", keyfile="cert.pem")
        self.context.load_verify_locations('cert.pem')
        self.context.set_ciphers('AES128-SHA')

        self.server_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((SERVER_HOST, port))
        self.server_socket.listen(backlog)
        self.server_socket = self.context.wrap_socket(self.server_socket, server_side=True)
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
                    inputs.append(client)

                    self.client_map[client] = (address, cname, time.time())
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

                            sock.close()
                            inputs.remove(sock)

                            self.outputs.remove(sock)
                            self.client_map.pop(sock)
                            self.clients -= 1

                        elif data[0] == "GET_ALL_CLIENTS":
                            send(sock, "CLIENTS", list(self.client_map.values()))

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
                            message = f"<< Client {self.get_client_name(sock)} has left the chat. >>"

                            try:
                                self.rooms[room_name].remove(sock)
                                print("sockets in room:", self.rooms[room_name])
                                if self.rooms[room_name]:
                                    for other_sock in self.rooms[room_name]:
                                        send(other_sock, message)
                                else:
                                    # If no one's left in the chat room, remove the room.
                                    self.rooms.pop(room_name)
                                    print(f"Room: {room_name} has been deleted.")

                            except KeyError:
                                print(f"Room: {room_name} does not exist.")

                            # A confirmation message. This closes fetch message thread waiting for incoming message.
                            send(sock, "EXITROOM_OK")

                        # Convention: ("MESSAGE", "room1", "Hello, World!")
                        elif data[0] == "MESSAGE":
                            # Send as new client's message...
                            # msg = f'{self.get_client_name(sock)}:{data}'
                            _, room_name, message = data
                            formatted_message = format_message(self.get_client_name(sock), message)

                            # Send data to all except ourself
                            for output in self.outputs:
                                if output != sock:
                                    send(output, formatted_message)

                        else:
                            print("Not sure what happened; Something strange happened in chat_server.py?")

                    except socket.error:
                        # Remove
                        inputs.remove(sock)
                        self.outputs.remove(sock)

        self.server_socket.close()
