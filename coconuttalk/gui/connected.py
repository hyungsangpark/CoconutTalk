from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QTextBrowser, QPushButton


class ConnectedWidget(QWidget):

    def __init__(self, ip_address: str, port: str, nickname: str) -> None:
        super().__init__()

        self.chat_rooms = QTextBrowser()
        self.connected_clients = QTextBrowser()
        self.ip_address: str = ip_address
        self.port: str = port
        self.nickname: str = nickname

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
        chat_button.clicked.connect(lambda: self.connected_clients.append("Hello World!"))

        main_layout.addWidget(QLabel("Chat rooms (Group Chat)"))

        chat_rooms_layout = QHBoxLayout()
        main_layout.addLayout(chat_rooms_layout)

        # Components inside chat_rooms_layout
        chat_rooms_layout.addWidget(self.chat_rooms)

        chat_rooms_buttons = QVBoxLayout()
        chat_rooms_layout.addLayout(chat_rooms_buttons)

        create_chat_room_button = QPushButton("Create", self)
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
