from PyQt5.QtCore import Qt, QCoreApplication, pyqtSlot
from PyQt5.QtWidgets import QWidget, QListWidget, QVBoxLayout, QLabel, QHBoxLayout, QListWidgetItem, QPushButton, \
    QInputDialog, QMessageBox

from coconuttalk.chat.chat_client import ChatClient
from coconuttalk.chat.utils import *
from coconuttalk.gui.fetch_utils import FetchClients
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

        self.fetch = FetchClients(client=self.client, parent=self)
        self.fetch.clients_fetched.connect(self.fill_clients)
        self.fetch.start()

    def init_ui(self) -> None:
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        main_layout.addWidget(QLabel("Connected Clients"))

        connected_clients_layout = QHBoxLayout()
        main_layout.addLayout(connected_clients_layout)

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
        close_button.clicked.connect(self.close_program)
        main_layout.addWidget(close_button)

        self.setWindowTitle("CoconutTalk")
        self.setGeometry(300, 300, 300, 200)
        self.show()

    @pyqtSlot(object)
    def fill_clients(self, clients: list[tuple[str, tuple[str, int]]]) -> None:
        print(f"clients to add: {clients}")

        connected_clients_ports: list[int] = [self.connected_clients.item(i).data(Qt.UserRole)[1] for i in
                                              range(self.connected_clients.count())]

        print(f"conneected_clients_port: {connected_clients_ports}")

        for client in clients:
            if client[1][1] in connected_clients_ports:
                client_index = connected_clients_ports.index(client[1][1])
                self.connected_clients.item(client_index).setText(client[0])
                connected_clients_ports[client_index] = -1
            else:
                new_client_list_widget_item = QListWidgetItem(client[0])
                # Convention: ("client_name", 13531)
                new_client_list_widget_item.setData(Qt.UserRole, client[1])
                self.connected_clients.addItem(new_client_list_widget_item)

        removed_elements = 0
        for i, port in enumerate(connected_clients_ports):
            if port != -1:
                self.connected_clients.takeItem(i - removed_elements)

    def one_to_one_chat(self) -> None:
        self.fetch.stop()
        self.fetch.wait()

        if self.connected_clients.currentItem() is None:
            notify_non_empty_nickname = QMessageBox()
            notify_non_empty_nickname.setText("Please select a user to chat.")
            notify_non_empty_nickname.exec()
            return

        client_to_chat_nickname, client_to_chat_port = self.connected_clients.currentItem().data(Qt.UserRole)
        print("address: " + client_to_chat_nickname)
        print("port: " + str(client_to_chat_port))

        result = ""
        created_room = False
        while not created_room:
            if result == "":
                send(self.client.sock, "CREATEROOM", f"{self.client.connected_port}_to_{client_to_chat_port}",
                     client_to_chat_port)
                result = receive(self.client.sock)[0]
            if result == "SUCCESS":
                created_room = True
            elif result == "EXISTS":
                send(self.client.sock, "JOINROOM", f"{self.client.connected_port}_to_{client_to_chat_port}")
                result = receive(self.client.sock)[0]
            elif result == "FAIL":
                notify_non_empty_nickname = QMessageBox()
                notify_non_empty_nickname.setText("Unknown error has occurred during creation of the room.")
                notify_non_empty_nickname.exec()
                return

        # Link to 1:1 chat and close connected screen.
        one_to_one_chat_dialog = OneToOneChatWidget(other_client_nickname=client_to_chat_nickname,
                                                    other_client_port=client_to_chat_port,
                                                    client=self.client,
                                                    parent=self)
        one_to_one_chat_dialog.exec()

        # Now that chat has finished, restart live-fetching the client list.
        self.fetch.start()

    def create_chatroom(self) -> None:
        """
        Creates a chat room that the client can join.
        """
        text, ok = QInputDialog.getText(self, 'Create Chat Room', "Enter new chat room name:")
        if ok:
            created_room = False
            while not created_room:
                send(self.client.sock, "CREATEROOM", text, -1)
                result = receive(self.client.sock)[0]
                if result == "SUCCESS":
                    created_room = True
                else:
                    text, _ = QInputDialog.getText(self,
                                                   "Create Chat Room",
                                                   "Chat room with the given name already exists.\n" +
                                                   "Enter a new chat room name:")
            self.chat_rooms.addItem(QListWidgetItem(text))

    def close_program(self) -> None:
        # self.client.cleanup()
        self.fetch.stop()
        QCoreApplication.instance().quit()
