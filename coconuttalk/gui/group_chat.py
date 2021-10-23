import time
from PyQt5.QtWidgets import QDialog, QTextBrowser, QVBoxLayout, QLabel, QHBoxLayout, QLineEdit, QPushButton, QGridLayout

from coconuttalk.chat.chat_client import ChatClient
from coconuttalk.chat.utils import Client
from coconuttalk.gui.fetch_utils import FetchMessage


class GroupChatDialog(QDialog):
    """
    This is a group chat window which allows users to chat with a single person.
    """

    def __init__(self, client: ChatClient, room_info: tuple[str, Client], parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Group Chat")

        self.client = client
        self.room_info = room_info
        self.room_name, self.room_host = self.room_info

        self.members = QTextBrowser()
        self.chats = QTextBrowser()
        self.chats_input = QLineEdit()

        self.init_ui()

        self.fetch_message_thread = FetchMessage(client=self.client, parent=self)
        self.fetch_message_thread.chat_fetched.connect(self.chats.append)
        self.fetch_message_thread.start()

    def init_ui(self) -> None:
        """
        Initializes UI of the window.
        """
        # Set up main layout
        main_layout = QGridLayout()
        main_layout.setColumnStretch(0, 3)
        main_layout.setColumnStretch(1, 1)
        main_layout.setColumnStretch(2, 1)
        self.setLayout(main_layout)

        # TODO: FOR DEBUG PURPOSES
        # self.chats.append("Alice (08:24): Hi!")
        # self.chats.append("James (08:25): Wow~")

        # TODO: FOR DEBUG PURPOSES
        # self.members.append("Alice (Host)")
        # self.members.append("James")

        self.members.append(f"{self.client.nickname}(me)")

        main_layout.addWidget(QLabel(f"{self.room_name} by {self.room_host[1]}"), 0, 0, 1, 2)
        main_layout.addWidget(QLabel("Members"), 0, 2)
        main_layout.addWidget(self.chats, 1, 0, 1, 2)
        main_layout.addWidget(self.members, 1, 2, 2, 1)

        main_layout.addWidget(self.chats_input, 2, 0)
        send_button = QPushButton("Send", self)
        send_button.clicked.connect(self.send)
        main_layout.addWidget(send_button, 2, 1)

        close_button = QPushButton("Close", self)
        close_button.clicked.connect(self.close_chat)
        main_layout.addWidget(close_button, 3, 0, 1, 2)
        invite_button = QPushButton("Invite", self)
        invite_button.clicked.connect(self.invite)
        main_layout.addWidget(invite_button, 3, 2)

    def close_chat(self) -> None:
        """
        Removes the chat in the server, then closes the chat.
        """
        self.fetch_message_thread.stop()
        # send("i'm leaving")
        self.client.leave_room(self.room_info)
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
            self.client.send_message(self.room_info, message)
            # send(self.client.sock, "MESSAGE", message)
            current_time = time.strftime("%H:%M", time.localtime())
            self.chats.append(f"Me ({current_time}): {message}")

    def invite(self):
        print("======== Invite is currently unimplemented. ========")