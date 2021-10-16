import select
import socket
import sys
import signal
import argparse

from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QTextBrowser, QPushButton, QListWidget, \
    QListWidgetItem, QInputDialog, QLineEdit, QGridLayout

from PyQt5.QtWidgets import QApplication


class ConnectedWidget(QWidget):

    def __init__(self, ip_address: str, port: str, nickname: str, client: ChatClient) -> None:
        super().__init__()

        self.chat_rooms = QListWidget()
        self.connected_clients = QListWidget()
        self.ip_address: str = ip_address
        self.port: str = port
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

    def __init__(self):
        super().__init__()
        self.nickname_line_edit = QLineEdit()
        self.port_line_edit = QLineEdit()
        self.ip_address_line_edit = QLineEdit()
        self.initUI()

    def initUI(self):
        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        main_layout.addStretch(1)

        input_grid = QGridLayout()
        main_layout.addLayout(input_grid)

        main_layout.addStretch(1)

        buttons_h_box = QHBoxLayout()
        main_layout.addLayout(buttons_h_box)

        # input_grid layout
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

        # buttons_h_box layout
        buttons_h_box.addStretch()

        connect_button = QPushButton("Connect", self)
        connect_button.clicked.connect(self.connect)
        buttons_h_box.addWidget(connect_button)

        cancel_button = QPushButton("Cancel", self)
        cancel_button.clicked.connect(QCoreApplication.instance().quit)
        buttons_h_box.addWidget(cancel_button)

        self.setWindowTitle("CoconutTalk")
        self.setGeometry(300, 300, 300, 200)
        self.show()

    def connect(self) -> None:

        ip_address = self.ip_address_line_edit.text()
        port: int = int(self.port_line_edit.text())
        nickname = self.nickname_line_edit.text()

        print(f"IP Address: {ip_address}")
        print(f"Port: {port}")
        print(f"Nickname: {nickname}")

        # Check whether a server pre-exists; use it if it exists, else create one.

        try:
            client = ChatClient(name=nickname, host=ip_address, port=port)
        except socket.error:
            #  extract this into a separate thread.
            # threading.Thread(target=lambda: ChatServer(host=ip_address, port=port))
            self.server = ChatServer(host=ip_address, port=port)

            client = ChatClient(name=nickname, host=ip_address, port=port)

        self.connected_widget = ConnectedWidget(ip_address, port, nickname, client)
        self.connected_widget.show()
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    connection_widget = ConnectionWidget()
    sys.exit(app.exec_())
