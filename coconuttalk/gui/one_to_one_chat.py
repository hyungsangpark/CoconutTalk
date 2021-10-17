import time

from PyQt5.QtWidgets import QDialog, QTextBrowser, QVBoxLayout, QLabel, QHBoxLayout, QLineEdit, QPushButton

from coconuttalk.chat.chat_client import ChatClient
from coconuttalk.chat.chat_utils import send


class OneToOneChatWidget(QDialog):
    def __init__(self, other_client_nickname: str, other_client_port: int, client: ChatClient,
                 parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("1:1 Chat")

        self.other_client_nickname = other_client_nickname
        self.other_client_port = other_client_port
        self.client = client

        self.chats = QTextBrowser()
        self.chats_input = QLineEdit()
        self.send_button = QPushButton("Send", self)

        self.init_ui()

    def init_ui(self) -> None:
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        main_layout.addWidget(QLabel(f"Chat with {self.other_client_nickname}"))
        main_layout.addWidget(self.chats)

        chats_container = QHBoxLayout()
        self.send_button.clicked.connect(self.send)
        chats_container.addWidget(self.chats_input, 7)
        chats_container.addWidget(self.send_button, 3)
        main_layout.addLayout(chats_container)

        close_button = QPushButton("Close", self)
        close_button.clicked.connect(self.accept)
        main_layout.addWidget(close_button)

    def close(self) -> None:
        """
        Removes the chat in the server, then closes the chat.
        :return: Remove chat
        """
        send(self.client.sock, f"CLOSEROOM:{self.client.connected_port}_to_{self.other_client_port}")
        self.close()

    def send(self) -> None:
        message: str = self.chats_input.text()
        print("Message sent: " + message)
        send(self.client.sock, message)

        current_time = time.strftime("%H:%M", time.localtime())
        self.chats.append(f"Me ({current_time}): {message}")

    def update(self) -> None:
        print()
