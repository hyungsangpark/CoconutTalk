import select
import signal
import socket
import ssl
import sys
import time

from coconuttalk.chat.utils import *


class ChatServer:
    """
    A chat server using select.

    Unique fields across the server are:
    - Client socket
    - A group chat room by per client.
    """

    def __init__(self, port, backlog=5):
        self.clients = 0
        self.client_map: dict[socket.socket, Client] = {}

        # dict[tuple[room_name, host_port], list[currently_connected_members]]
        self.group_chat_rooms: dict[tuple[str, Client], list[socket.socket]] = {}
        self.one_to_one_chat_rooms: dict[socket.socket, socket.socket] = {}

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
                    client_socket, address = self.server_socket.accept()
                    print(
                        f'Chat server: got connection {client_socket.fileno()} from {address}')
                    # Read the login name
                    cname: str = receive(client_socket)[1]

                    # Compute client name and send back
                    self.clients += 1
                    client: Client = (address, cname, time.time())
                    print(f"newly connected client: {client}")
                    send(client_socket, "CLIENT", client)
                    inputs.append(client_socket)

                    self.client_map[client_socket] = client
                    self.outputs.append(client_socket)

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

                        elif data[0] == "GET_UPDATES":
                            print("UPDATE REQUEST RECEIVED")
                            # group_chat_room_names: list[tuple[str, Client]] = ()

                            # group_chat_room_names = list(map(lambda room: (room[0], self.client_map[self.get_client_socket(room[1])]), self.group_chat_rooms.keys()))
                            print(f"group_chat_room_names: {list(self.group_chat_rooms.keys())}")
                            send(sock, "CLIENTS", list(self.client_map.values()), "ROOMS", list(self.group_chat_rooms.keys()))

                        # Convention: ("CONNECT_ONE_TO_ONE", 13531)
                        elif data[0] == "CONNECT_ONE_TO_ONE":
                            _, chatting_client_port = data
                            # message = ""
                            return_code = "SUCCESS"
                            try:
                                # _ = self.rooms[room_name]
                                _ = self.one_to_one_chat_rooms[sock]
                                # message = "Room with given name already exists. Please try a different name."
                                # return_code = "EXISTS"
                            except KeyError:
                                # self.rooms[room_name] = [sock]
                                # self.rooms[room_name].append(self.get_client_socket(chatting_client_port))

                                chatting_client_socket = self.get_client_socket(chatting_client_port)
                                self.one_to_one_chat_rooms[sock] = chatting_client_socket
                                self.one_to_one_chat_rooms[chatting_client_socket] = sock

                                # if chatting_client_port != -1:
                                # message = f"Room: {room_name} has been created."
                                # return_code = "SUCCESS"
                            finally:
                                # print(message)
                                send(sock, return_code)

                        elif data[0] == "END_ONE_TO_ONE":
                            try:
                                other_sock = self.one_to_one_chat_rooms.pop(sock)
                                self.one_to_one_chat_rooms.pop(other_sock)

                                message = f"<< Client {self.get_client_name(sock)} has left the chat. >>"

                                send(other_sock, message)
                            except KeyError as e:
                                # Consume the exception as this means the connection has already been closed.
                                _ = e

                            send(sock, "EXITROOM_OK")
                            #
                            # # TODO: Complete this section
                            # print("hi")

                        # Convention: ("CREATEROOM", "room_name_hehe_xd", 13531)
                        elif data[0] == "CREATEROOM":
                            # _, room_name, chatting_client_port = data
                            _, room_name, host = data
                            message = ""
                            return_code = ""
                            try:
                                # _ = self.rooms[room_name]
                                _ = self.group_chat_rooms[(room_name, host)]
                                message = "Room with given name already exists. Please try a different name."
                                return_code = "EXISTS"
                            except KeyError:
                                # self.rooms[room_name] = [sock]
                                # if chatting_client_port != -1:
                                #     self.rooms[room_name].append(self.get_client_socket(chatting_client_port))
                                self.group_chat_rooms[(room_name, host)] = []
                                message = f"Room: {room_name} has been created."
                                return_code = "SUCCESS"
                            finally:
                                print(message)
                                send(sock, return_code)

                        elif data[0] == "JOINROOM":
                            _, room_info = data
                            return_code = "UNKNOWN_ERROR"

                            try:
                                # self.rooms[room_name].append(sock)
                                print(f"room to join: {room_info}")
                                print(f"list of rooms: {list(self.group_chat_rooms.keys())}")
                                self.group_chat_rooms[room_info].append(sock)
                                return_code = "SUCCESS"
                            except KeyError:
                                return_code = "NO_SUCH_ROOM"
                            finally:
                                print(return_code)
                                send(sock, return_code)

                        # Convention: ("CLOSEROOM", "room_name_hehe_xd")
                        elif data[0] == "EXITROOM":
                            # Change this.
                            _, room_info = data
                            message = f"<< Client {self.get_client_name(sock)} has left the chat. >>"

                            try:
                                connected_clients = self.group_chat_rooms[room_info]
                                connected_clients.remove(sock)
                                print("sockets in room after removal:", connected_clients)

                                if connected_clients:
                                    for other_sock in connected_clients:
                                        send(other_sock, message)

                                else:
                                    # If no one's left in the chat room, remove the room.
                                    self.group_chat_rooms.pop(room_info)
                                    print(f"Room: {room_info[0]} by {room_info[1][1]} has been deleted.")

                            except KeyError:
                                print(f"Room: {room_info[0]} by {room_info[1][1]} does not exist.")

                            # A confirmation message. This closes fetch message thread waiting for incoming message.
                            send(sock, "EXITROOM_OK")

                        elif data[0] == "CLIENTS_IN_ROOM":
                            # TODO: send clients given room info.
                            _, room_info = data

                            clients: list[Client] = []
                            # return_code = "UNKNOWN_ERROR"

                            try:
                                # clients_socket = self.group_chat_rooms[room_info]
                                clients = [self.client_map[member] for member in self.group_chat_rooms[room_info]]
                                print(f"clients: {clients}")
                                return_code = "SUCCESS"
                            except KeyError:
                                return_code = "NO_SUCH_ROOM"

                            send(sock, return_code, clients)

                        # Convention: ("MESSAGE", "room1", "Hello, World!")
                        elif data[0] == "MESSAGE":
                            # Send as new client's message...
                            # msg = f'{self.get_client_name(sock)}:{data}'
                            _, room_info, message = data
                            formatted_message = format_message(self.get_client_name(sock), message)

                            print(f"trying to send the message ({message}) to room {room_info[0]}")

                            try:
                                socket_to_send = self.one_to_one_chat_rooms[sock]
                                print(f"one to one socket found, sending to socket: {socket_to_send}")
                                send(socket_to_send, formatted_message)
                            except KeyError as e:
                                _ = e
                                print("one to one socket not found, trying group chat socket.")
                                for room in self.group_chat_rooms.values():
                                    print(f"room: {room}")
                                    if sock in room:
                                        print("room with sender socket found")
                                        for other_sock in room:
                                            print(f"other_sock: {other_sock}")
                                            if other_sock != sock:
                                                # Send formatted message to every other people.
                                                send(other_sock, formatted_message)
                                        break



                            # # Send data to all except ourself
                            # for output in self.outputs:
                            #     if output != sock:
                            #         send(output, formatted_message)

                        else:
                            print("Not sure what happened; Something strange happened in chat_server.py?")

                    except socket.error:
                        # Remove
                        inputs.remove(sock)
                        self.outputs.remove(sock)

        self.server_socket.close()
