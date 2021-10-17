import time

from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtWidgets import QWidget, QListWidget, QVBoxLayout, QLabel, QHBoxLayout, QListWidgetItem, QPushButton, \
    QInputDialog

from coconuttalk.chat.chat_client import ChatClient
from coconuttalk.chat.chat_utils import *
from coconuttalk.gui.one_to_one_chat import OneToOneChatWidget


class ConnectedWidget(QWidget):

    def __init__(self, client: ChatClient) -> None:
        super().__init__()

        self.chat_rooms = QListWidget()
        self.connected_clients = QListWidget()
        self.port: int = -1
        self.client: ChatClient = client
        self.one_to_one_chat_widgets = []

        self.init_ui()

    def init_ui(self) -> None:
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        main_layout.addWidget(QLabel("Connected Clients"))

        connected_clients_layout = QHBoxLayout()
        main_layout.addLayout(connected_clients_layout)

        # Components inside connected_clients_layout
        # self.connected_clients.addItem(QListWidgetItem(f"{self.client.name} [me] (now)"))

        # Retrieve a list of clients currently connected and list them in the list of clients.
        clients = self.client.get_all_clients()
        # myself = next(client for client in clients if client[1] == self.client.nickname)
        # self.port = myself[0][1]
        clients.remove(next(client for client in clients if client[1] == self.client.nickname))
        # clients = list(filter(lambda c: c[1] != self.client.name, clients))
        current_time = time.time()
        clients.append((
            (self.client.server_address, self.client.server_port),
            f"{self.client.nickname} [me]",
            current_time))

        for client in clients:
            seconds_elapsed = current_time - client[2]
            hours, rest = divmod(seconds_elapsed, 3600)
            mins, secs = divmod(rest, 60)
            if hours > 0:
                time_passed = f"{int(hours)} hour ago"
            elif mins > 0:
                time_passed = f"{int(mins)} min ago"
            elif secs == 0:
                time_passed = "now"
            else:
                time_passed = f"{int(secs)} sec ago"

            client_list_widget_item = QListWidgetItem(f"{client[1]} ({time_passed})")
            client_list_widget_item.setData(Qt.UserRole, client[0][1])
            self.connected_clients.addItem(client_list_widget_item)

        self.connected_clients.currentItem()

        connected_clients_layout.addWidget(self.connected_clients)
        chat_button = QPushButton("1:1 Chat", self)
        connected_clients_layout.addWidget(chat_button)
        # TODO: Modify this to a proper listener behaviour.
        chat_button.clicked.connect(self.one_to_one_chat)

        main_layout.addWidget(QLabel("Chat rooms (Group Chat)"))

        chat_rooms_layout = QHBoxLayout()
        main_layout.addLayout(chat_rooms_layout)

        # Components inside chat_rooms_layout
        chat_rooms_layout.addWidget(self.chat_rooms)

        chat_rooms_buttons = QVBoxLayout()
        chat_rooms_layout.addLayout(chat_rooms_buttons)

        create_chat_room_button = QPushButton("Create", self)
        create_chat_room_button.clicked.connect(self.create_chatroom)
        chat_rooms_buttons.addWidget(create_chat_room_button)
        join_chat_room_button = QPushButton("Join", self)
        chat_rooms_buttons.addWidget(join_chat_room_button)

        close_button = QPushButton("Close", self)
        close_button.clicked.connect(QCoreApplication.instance().quit)
        main_layout.addWidget(close_button)

        main_layout.addWidget(QLabel(f"IP Address: {self.client.server_address}"))
        main_layout.addWidget(QLabel(f"Port: {self.client.server_port}"))
        main_layout.addWidget(QLabel(f"Nickname: {self.client.nickname}"))

        self.setWindowTitle("CoconutTalk")
        self.setGeometry(300, 300, 300, 200)
        self.show()

    def one_to_one_chat(self) -> None:
        client_to_chat_port = self.connected_clients.currentItem().data(Qt.UserRole)
        client_to_chat_nickname = self.connected_clients.currentItem().text().rpartition(' (')[0]
        print("port: " + str(client_to_chat_port))

        created_room = False
        while not created_room:
            send(self.client.sock, f"CREATEROOM:{self.client.connected_port}_to_{client_to_chat_port}:{client_to_chat_port}")
            result = receive(self.client.sock)
            if result == "SUCCESS":
                created_room = True

        # Link to 1:1 chat and close connected screen.
        one_to_one_chat_dialog = OneToOneChatWidget(nickname=self.client.nickname,
                                                    other_client_nickname=client_to_chat_nickname,
                                                    other_client_port=client_to_chat_port,
                                                    client=self.client,
                                                    parent=self)
        one_to_one_chat_dialog.exec()

    def create_chatroom(self) -> None:
        text, ok = QInputDialog.getText(self, 'Create Chat Room', "Enter new chat room name:")
        if ok:
            created_room = False
            while not created_room:
                send(self.client.sock, f"CREATEROOM:{text}:null")
                result = receive(self.client.sock)
                if result == "SUCCESS":
                    created_room = True
                else:
                    text, _ = QInputDialog.getText(self,
                                                   "Create Chat Room",
                                                   "Chat room with the given name already exists.\n" +
                                                   "Enter a new chat room name:")
            self.chat_rooms.addItem(QListWidgetItem(text))
