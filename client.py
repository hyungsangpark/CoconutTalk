import select
import socket
import sys

from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QListWidget,
                             QListWidgetItem, QInputDialog, QLineEdit, QGridLayout)

from utils import *

SERVER_HOST = "localhost"


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
        except socket.error as e:
            print(f'Failed to connect to chat server @ port {self.port}')
            sys.exit(1)

    def getallclients(self) -> list[tuple[tuple[str, int], str]]:
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


class ConnectedWidget(QWidget):

    def __init__(self, ip_address: str, port: int, nickname: str, client: ChatClient) -> None:
        super().__init__()

        self.chat_rooms = QListWidget()
        self.connected_clients = QListWidget()
        self.ip_address: str = ip_address
        self.port: int = port
        self.nickname: str = nickname
        self.client: ChatClient = client

        self.initUI()

    def initUI(self) -> None:
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        main_layout.addWidget(QLabel("Connected Clients"))

        connected_clients_layout = QHBoxLayout()
        main_layout.addLayout(connected_clients_layout)

        # Components inside connected_clients_layout
        # self.connected_clients.addItem(QListWidgetItem(f"{self.nickname} [me] (now)"))

        clients = self.client.getallclients()
        clients.append(((self.ip_address, self.port), f"{self.nickname} [me] (now)"))

        for client in clients:
            self.connected_clients.addItem(QListWidgetItem(f"{client[1]}"))

        connected_clients_layout.addWidget(self.connected_clients)
        chat_button = QPushButton("1:1 Chat", self)
        connected_clients_layout.addWidget(chat_button)
        # TODO: Modify this to a proper listener behaviour.
        chat_button.clicked.connect(lambda: self.connected_clients.addItem(QListWidgetItem("Hii")))

        main_layout.addWidget(QLabel("Chat rooms (Group Chat)"))

        chat_rooms_layout = QHBoxLayout()
        main_layout.addLayout(chat_rooms_layout)

        # Components inside chat_rooms_layout
        chat_rooms_layout.addWidget(self.chat_rooms)

        chat_rooms_buttons = QVBoxLayout()
        chat_rooms_layout.addLayout(chat_rooms_buttons)

        create_chat_room_button = QPushButton("Create", self)
        create_chat_room_button.clicked.connect(self.createChatRoom)
        chat_rooms_buttons.addWidget(create_chat_room_button)
        join_chat_room_button = QPushButton("Join", self)
        chat_rooms_buttons.addWidget(join_chat_room_button)

        close_button = QPushButton("Close", self)
        close_button.clicked.connect(QCoreApplication.instance().quit)
        main_layout.addWidget(close_button)

        main_layout.addWidget(QLabel(f"IP Address: {self.ip_address}"))
        main_layout.addWidget(QLabel(f"Port: {self.port}"))
        main_layout.addWidget(QLabel(f"Nickname: {self.nickname}"))

        self.setWindowTitle("CoconutTalk")
        self.setGeometry(300, 300, 300, 200)
        self.show()

    def createChatRoom(self) -> None:
        text, ok = QInputDialog.getText(self, 'Create Chat Room', "Enter new chat room name:")
        if ok:
            self.chat_rooms.addItem(QListWidgetItem(text))


class ConnectionWidget(QWidget):
    """
    A PyQT5 widget for connection screen.
    """

    def __init__(self):
        super().__init__()
        self.nickname_line_edit = QLineEdit()
        self.port_line_edit = QLineEdit()
        self.ip_address_line_edit = QLineEdit()
        self.initUI()

    def initUI(self) -> None:
        """
        Initializes the UI of the program and displays it.
        """

        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        main_layout.addStretch(1)

        # input_grid layout
        input_grid = QGridLayout()

        ip_address_label = QLabel("IP Address")
        port_label = QLabel("Port")
        nickname_label = QLabel("Nickname")
        input_grid.addWidget(ip_address_label, 0, 0)
        input_grid.addWidget(port_label, 1, 0)
        input_grid.addWidget(QLabel(), 2, 0)
        input_grid.addWidget(nickname_label, 3, 0)

        input_grid.addWidget(self.ip_address_line_edit, 0, 1)
        input_grid.addWidget(self.port_line_edit, 1, 1)
        input_grid.addWidget(self.nickname_line_edit, 3, 1)

        # Add input_grid to main_layout.
        main_layout.addLayout(input_grid)

        # Add spacer between input section and buttons section.
        main_layout.addStretch(1)

        # buttons_h_box layout
        buttons_h_box = QHBoxLayout()

        # Spacer on left side of the buttons HBox.
        buttons_h_box.addStretch()

        connect_button = QPushButton("Connect", self)
        connect_button.clicked.connect(self.connect)
        buttons_h_box.addWidget(connect_button)

        cancel_button = QPushButton("Cancel", self)
        cancel_button.clicked.connect(QCoreApplication.instance().quit)
        buttons_h_box.addWidget(cancel_button)

        # Add buttons_h_box to main_layout.
        main_layout.addLayout(buttons_h_box)

        # Set window properties of this widget application and show it.
        self.setWindowTitle("CoconutTalk")
        self.setGeometry(300, 300, 300, 200)
        self.show()

    def connect(self) -> None:
        """
        Connects the client to the server with the given input field values.
        This is a Connect button on-click handler.
        """
        ip_address = self.ip_address_line_edit.text()
        port: int = int(self.port_line_edit.text())
        nickname = self.nickname_line_edit.text()

        print(f"IP Address: {ip_address}")
        print(f"Port: {port}")
        print(f"Nickname: {nickname}")

        client = ChatClient(name=nickname, host=ip_address, port=port)

        self.connected_widget = ConnectedWidget(ip_address, port, nickname, client)
        self.connected_widget.show()
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    connection_widget = ConnectionWidget()
    sys.exit(app.exec_())
