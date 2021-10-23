import select
import ssl

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

        # Create SSL Context for Chat Client.
        self.context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)

        # Initial prompt
        self.prompt = f'[{nickname}@{socket.gethostname()}]> '

        # Connect to server at port
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock = self.context.wrap_socket(self.sock, server_hostname=host)
            self.sock.connect((host, self.server_port))
            print(f'Now connected to chat server@ port {self.server_port}')
            self.connected = True

            # Send my name.
            # Convention: ("NAME", "hyung")
            send(self.sock, "NAME", self.nickname)

            # Receive client address.
            # Convention: ("CLIENT", (('127.0.0.1', 15151), "hyung", 12532.2390523))
            self.client_object_from_server = receive(self.sock)[1]
            self.connected_address, self.connected_port = self.client_object_from_server[0]

            # Contains client address, set it
            # print("received address data: " + data)
            # self.connected_address, connected_port_str = data.split('CLIENT: ')[1].split(":")
            # self.connected_port = int(connected_port_str)
            # self.prompt = '[' + '@'.join((self.nickname, self.connected_address)) + ']> '
        except socket.error:
            print(f'Failed to connect to chat server @ port {self.server_port}')
            raise socket.error

    def get_server_update(self) -> tuple[list[Client], list[str, Client]]:
        """
        Retrieves list of clients currently connected to the server.
        :return: A tuple with list of client information
        """
        client_description: str = ""
        clients: list[Client] = []
        rooms_description: str = ""
        group_chat_rooms: list[str, Client] = []
        while client_description != "CLIENTS" or rooms_description != "ROOMS":
            send(self.sock, "GET_UPDATES")
            try:
                client_description, clients, rooms_description, group_chat_rooms = receive(self.sock)
            except ValueError:
                print("Something unexpected received while receiving server updates. Please try again.")
                continue
        return clients, group_chat_rooms

    def cleanup(self):
        """
        Close the connection and wait for the thread to terminate.
        :return:
        """
        self.sock.close()

    def leave_one_to_one(self) -> None:
        send(self.sock, "END_ONE_TO_ONE")

    def join_room(self, room_info: tuple[str, Client]) -> None:
        try_counter = 0
        while try_counter < 5:
            print(f"Try {try_counter} of joining ROOM: {room_info[0]} by {room_info[1][1]}")
            send(self.sock, "JOINROOM", room_info)
            result, = receive(self.sock)
            print(f"RESULT(try {try_counter}): {result}")

            if result == "SUCCESS":
                break
            else:
                try_counter += 1

        print(f"JOIN SUCCESS AFTER {try_counter} TRY" if try_counter < 5 else "JOIN FAILED AFTER 5 TRIES")

    def leave_room(self, room_info: tuple[str, Client]) -> None:
        send(self.sock, "EXITROOM", room_info)

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

    def send_message(self, room_info: tuple[str, Client], message: str) -> None:
        send(self.sock, "MESSAGE", room_info, message)
