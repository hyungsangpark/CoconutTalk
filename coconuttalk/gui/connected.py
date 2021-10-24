from PyQt5.QtCore import Qt, QCoreApplication, pyqtSlot
from PyQt5.QtWidgets import QWidget, QListWidget, QVBoxLayout, QLabel, QHBoxLayout, QListWidgetItem, QPushButton, \
    QInputDialog, QMessageBox

from coconuttalk.chat.chat_client import ChatClient
from coconuttalk.chat.utils import *
from coconuttalk.gui.fetch_utils import FetchServerUpdates
from coconuttalk.gui.group_chat import GroupChatDialog
from coconuttalk.gui.one_to_one_chat import OneToOneChatDialog


class ConnectedWidget(QWidget):

    def __init__(self, client: ChatClient) -> None:
        super().__init__()

        self.chat_rooms = QListWidget()
        self.connected_clients = QListWidget()
        self.port: int = -1
        self.client: ChatClient = client
        self.one_to_one_chat_widgets = []

        self.init_ui()

        self.fetch = FetchServerUpdates(client=self.client, parent=self)
        self.fetch.updates_fetched.connect(self.apply_server_updates)
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
        join_chat_room_button.clicked.connect(self.join_room)
        chat_rooms_buttons.addWidget(join_chat_room_button)

        close_button = QPushButton("Close", self)
        close_button.clicked.connect(self.close_program)
        main_layout.addWidget(close_button)

        self.setWindowTitle("CoconutTalk")
        self.setGeometry(300, 300, 300, 200)
        self.show()

    @pyqtSlot(object)
    def apply_server_updates(self, updates: tuple[ list[tuple[str, tuple[str, int]]], list[tuple[str, Client]] ]) -> None:
        clients, group_chat_rooms = updates

        # print(f"clients to add: {clients}")

        # Start applying currently connected clients.

        connected_clients_ports: list[int] = [self.connected_clients.item(i).data(Qt.UserRole)[1] for i in
                                              range(self.connected_clients.count())]

        # print(f"conneected_clients_port: {connected_clients_ports}")

        for client in clients:
            if client[1][1] in connected_clients_ports:
                # Retrieve current index of the client in the QListWidget.
                client_index = connected_clients_ports.index(client[1][1])
                # Set text to the current client in the QListWidget.
                self.connected_clients.item(client_index).setText(client[0])
                connected_clients_ports[client_index] = -1
            else:
                new_client_list_widget_item = QListWidgetItem(client[0])
                # Convention: ("client_name", 13531)
                new_client_list_widget_item.setData(Qt.UserRole, client[1])
                self.connected_clients.addItem(new_client_list_widget_item)

        # print(f"connected_clients_ports after update: {connected_clients_ports}")
        removed_elements = 0
        for i, port in enumerate(connected_clients_ports):
            # print(f"current port: {port}")
            if port != -1:
                self.connected_clients.takeItem(i - removed_elements)
                removed_elements += 1

        # Start applying current list of group chats.

        already_present_group_chats: list[tuple[str, Client]] = [self.chat_rooms.item(i).data(Qt.UserRole) for i in range(self.chat_rooms.count())]
        # print(f"already present chats: {already_present_group_chats}")
        # updated_group_chats: list[str, Client] = [room for room in group_chat_rooms]

        rooms_to_add = list(set(group_chat_rooms) - set(already_present_group_chats))
        rooms_to_remove = list(set(already_present_group_chats) - set(group_chat_rooms))

        # print(f"rooms_to_add: {rooms_to_add}")
        # print(f"rooms_to_remove: {rooms_to_remove}")

        for room in rooms_to_add:
            new_room_to_add = QListWidgetItem(f"{room[0]} by {room[1][1]}")
            new_room_to_add.setData(Qt.UserRole, room)
            self.chat_rooms.addItem(new_room_to_add)

        # removed_elements = 0
        for removed_rooms, room in enumerate(rooms_to_remove):
            room_index = already_present_group_chats.index(room)
            self.chat_rooms.takeItem(room_index - removed_rooms)

    def one_to_one_chat(self) -> None:
        self.fetch.stop()
        self.fetch.wait()

        if self.connected_clients.currentItem() is None:
            notify_non_empty_nickname = QMessageBox()
            notify_non_empty_nickname.setText("Please select a user to chat.")
            notify_non_empty_nickname.exec()
            return

        client_to_chat_nickname, client_to_chat_port = self.connected_clients.currentItem().data(Qt.UserRole)
        # print("address: " + client_to_chat_nickname)
        # print("port: " + str(client_to_chat_port))

        result = ""
        created_room = False
        while not created_room:
            if result == "":
                send(self.client.sock, "CONNECT_ONE_TO_ONE", client_to_chat_port)
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
        one_to_one_chat_dialog = OneToOneChatDialog(other_client_nickname=client_to_chat_nickname,
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
        room_name, ok = QInputDialog.getText(self, 'Create Chat Room', "Enter new chat room name:")
        if ok:
            created_room = False
            while not created_room:
                send(self.client.sock, "CREATEROOM", room_name, self.client.client_object_from_server)
                result = receive(self.client.sock)[0]
                if result == "SUCCESS":
                    created_room = True
                else:
                    room_name, continue_room_creation = QInputDialog.getText(self,
                                                        "Create Chat Room",
                                                        "Chat room with the given name already exists.\n" +
                                                        "Enter a new chat room name:")
                    if not continue_room_creation:
                        return

            new_chat_room_item = QListWidgetItem(f"{room_name} by {self.client.nickname}")
            # client: Client = ((self.client.connected_address, self.client.connected_port), self.client.nickname, 0.0)
            new_chat_room_item.setData(Qt.UserRole, (room_name, self.client.client_object_from_server))
            self.chat_rooms.addItem(new_chat_room_item)

    def join_room(self) -> None:
        self.fetch.stop()
        self.fetch.wait()

        if self.chat_rooms.currentItem() is None:
            notify_unselected_chat_room = QMessageBox()
            notify_unselected_chat_room.setText("Please select a room to join.")
            notify_unselected_chat_room.exec()
            return

        chat_room_info = self.chat_rooms.currentItem().data(Qt.UserRole)
        # print(f"chat room name: {chat_room_info[0]}")
        # print(f"chat room host: {chat_room_info[1]}")

        self.client.join_room(chat_room_info)

        # Link to 1:1 chat and close connected screen.
        one_to_one_chat_dialog = GroupChatDialog(client=self.client,
                                                 room_info=chat_room_info,
                                                 parent=self)
        one_to_one_chat_dialog.exec()

        # Now that chat has finished, restart live-fetching the client list.
        self.fetch.start()

    def close_program(self) -> None:
        # self.client.cleanup()
        self.fetch.stop()
        self.fetch.wait()
        QCoreApplication.instance().quit()
