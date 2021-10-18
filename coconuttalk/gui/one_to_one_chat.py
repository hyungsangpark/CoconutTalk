import time
from PyQt5.QtWidgets import QDialog, QTextBrowser, QVBoxLayout, QLabel, QHBoxLayout, QLineEdit, QPushButton

from coconuttalk.chat.chat_client import ChatClient
from coconuttalk.chat.utils import send
from coconuttalk.gui.fetch_utils import FetchMessage


class OneToOneChatWidget(QDialog):
    """
    This is a 1:1 chat window which allows users to chat with a single person.
    """

    def __init__(self, other_client_nickname: str, other_client_port: int, client: ChatClient,
                 parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("1:1 Chat")

        self.other_client_nickname = other_client_nickname
        self.other_client_port = other_client_port
        self.client = client
        self.room_name = f"{self.client.connected_port}_to_{self.other_client_port}"

        self.chats = QTextBrowser()
        self.chats_input = QLineEdit()
        self.send_button = QPushButton("Send", self)

        self.init_ui()

        self.fetch_message_thread = FetchMessage(client=self.client, parent=self)
        self.fetch_message_thread.chat_fetched.connect(self.chats.append)
        self.fetch_message_thread.start()

    def init_ui(self) -> None:
        """
        Initializes UI of the window.
        """
        # Set up main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Add main header of the window.
        main_layout.addWidget(QLabel(f"Chat with {self.other_client_nickname}"))
        main_layout.addWidget(self.chats)

        # Add the chat container with list of chats
        chats_container = QHBoxLayout()

        # Add send button and input
        self.send_button.clicked.connect(self.send)
        chats_container.addWidget(self.chats_input, 7)
        chats_container.addWidget(self.send_button, 3)
        main_layout.addLayout(chats_container)

        # Add close button
        close_button = QPushButton("Close", self)
        close_button.clicked.connect(self.close_chat)
        main_layout.addWidget(close_button)

    def close_chat(self) -> None:
        """
        Removes the chat in the server, then closes the chat.
        """
        self.fetch_message_thread.stop()
        # send("i'm leaving")
        self.client.leave_room(self.room_name)
        self.accept()

    def send(self) -> None:
        """
        Sends a message in chat input field to the chatting client.
        """
        # Retrieve message and clear chat input.
        message: str = self.chats_input.text()
        self.chats_input.clear()
        print("Message sent: " + message)

        # Only send message if it's not empty.
        if message:
            # Convention: ("MESSAGE", "Hello, world!")
            self.client.send_message(self.room_name, message)
            # send(self.client.sock, "MESSAGE", message)
            current_time = time.strftime("%H:%M", time.localtime())
            self.chats.append(f"Me ({current_time}): {message}")
