import time
from threading import Thread

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QDialog, QTextBrowser, QVBoxLayout, QLabel, QHBoxLayout, QLineEdit, QPushButton

from coconuttalk.chat.chat_client import ChatClient
from coconuttalk.chat.utils import send


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

        self.fetch_message_thread = FetchMessage(client=self.client)
        self.fetch_message_thread.chat_fetched.connect(self.add_chat)
        self.fetch_message_thread.start()

        # self.fetch_message_thread_alive = True
        # self.fetch_message_thread = Thread(target=self.fetch_message, args=(lambda: self.fetch_message_thread_alive,))
        # self.fetch_message_thread.start()

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
        close_button.clicked.connect(self.close_chat)
        main_layout.addWidget(close_button)

    # def fetch_message(self, is_thread_alive) -> None:
    #     print("Start Thread!")
    #     while True:
    #         time.sleep(2)
    #         print("yes, thread is running...")
    #         self.chats.append("James (08:23): Yes, thread is running...")
    #         if not is_thread_alive():
    #             break
    #     print("thread ended.")

    def add_chat(self, message) -> None:
        print(message)
        self.chats.append(message)

    def close_chat(self) -> None:
        """
        Removes the chat in the server, then closes the chat.
        :return: Remove chat
        """
        self.fetch_message_thread.stop()
        send(self.client.sock, f"CLOSEROOM:{self.client.connected_port}_to_{self.other_client_port}")
        self.accept()

    def send(self) -> None:
        message: str = self.chats_input.text()
        print("Message sent: " + message)
        if message:
            send(self.client.sock, message)
            current_time = time.strftime("%H:%M", time.localtime())
            self.chats.append(f"Me ({current_time}): {message}")


class FetchMessage(QThread):
    chat_fetched = pyqtSignal(object)

    def __init__(self, client: ChatClient, parent=None):
        super(FetchMessage, self).__init__(parent)
        self.thread_alive = True
        self.client = client

    def run(self):
        print("Start Thread!")
        while self.thread_alive:
            messages: list[str] = self.client.fetch_messages()
            for message in messages:
                if message.startswith("SHUTDOWN:"):
                    self.chat_fetched.emit()
            [self.chat_fetched.emit(message) for message in messages]
            # self.chats.append("James (08:23): Yes, thread is running...")

    def stop(self):
        self.thread_alive = False
