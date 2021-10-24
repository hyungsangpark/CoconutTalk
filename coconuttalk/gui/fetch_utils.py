import time

from PyQt5.QtCore import QThread, pyqtSignal

from coconuttalk.chat.chat_client import ChatClient
from coconuttalk.chat.chat_utils import Client


class FetchGroupMessage(QThread):
    """
    Fetches messages to the client,
    and emits fetched list of chats messages to the connected listener. (FetchMessage#chat_fetched)
    """
    chat_fetched = pyqtSignal(object)
    members_fetched = pyqtSignal(object)

    def __init__(self, client: ChatClient, room_info: tuple[str, Client] = None, parent=None):
        super(FetchGroupMessage, self).__init__(parent)
        self.client = client
        self.room_info = room_info
        self.thread_alive = False

    def run(self):
        """
        Method that runs when FetchMessage#start() is run.

        It runs in a loop that continuously fetches messages in real time.
        """
        self.thread_alive = True
        # print("Fetch Message Thread alive!")

        # Iterate until the thread is considered dead.
        while self.thread_alive:
            # Fetch messages and emit each message to the connected listener.
            # Merge them to both.
            chat_client_list: list[Client] = self.client.fetch_clients_in_room(self.room_info)
            # print(f"clients in chat to emit: {chat_client_list}")
            self.members_fetched.emit(chat_client_list)

            messages: list[str] = self.client.fetch_messages()
            # print(f"messages to emit: {messages}")
            [self.chat_fetched.emit(message) for message in messages]

            # if self.room_info:

    def stop(self):
        """
        Stops the thread.
        """
        self.thread_alive = False


class FetchMessage(QThread):
    """
    Fetches messages to the client,
    and emits fetched list of chats messages to the connected listener. (FetchMessage#chat_fetched)
    """
    chat_fetched = pyqtSignal(object)

    def __init__(self, client: ChatClient, parent=None):
        super(FetchMessage, self).__init__(parent)
        self.client = client
        self.thread_alive = False

    def run(self):
        """
        Method that runs when FetchMessage#start() is run.

        It runs in a loop that continuously fetches messages in real time.
        """
        self.thread_alive = True
        # print("Fetch Message Thread alive!")

        # Iterate until the thread is considered dead.
        while self.thread_alive:
            # Fetch messages and emit each message to the connected listener.
            messages: list[str] = self.client.fetch_messages()
            # print(f"messages to emit: {messages}")
            [self.chat_fetched.emit(message) for message in messages]

    def stop(self):
        """
        Stops the thread.
        """
        self.thread_alive = False


class FetchServerUpdates(QThread):
    """
    Fetches list of clients currently connected in the server,
    and emits fetched list of clients to the connected listener. (FetchClients#clients_fetched)
    """
    updates_fetched = pyqtSignal(object)

    def __init__(self, client: ChatClient, parent=None):
        super(FetchServerUpdates, self).__init__(parent)
        self.client = client
        self.thread_alive = False

    def run(self):
        self.thread_alive = True
        # print("Fetch Server Update Thread Started!")

        # Iterate until the thread is considered dead.
        while self.thread_alive:
            clients: list[tuple[str, tuple[str, int]]] = []
            # updates: tuple[list[tuple[str, tuple[str, int]]], list[str]]

            # Retrieve a list of clients currently connected and list them in the list of clients.
            connected_clients, group_chat_rooms = self.client.get_server_update()
            # print(f"connected_clients: {connected_clients}")

            # Format each client information into client information form used for clients list.
            current_time = time.time()
            for client in connected_clients:
                seconds_elapsed = current_time - client[2]
                hours, rest = divmod(seconds_elapsed, 3600)
                minutes, seconds = divmod(rest, 60)

                # Add appropriate time elapsed label.
                if hours > 0:
                    time_passed = f"{int(hours)} hour ago"
                elif minutes > 0:
                    time_passed = f"{int(minutes)} min ago"
                elif seconds > 1:
                    time_passed = f"{int(seconds)} sec ago"
                else:
                    time_passed = "now"

                # Possibly add [me] label if it's the person.
                me_notifier = " [me]" if client[0][1] == self.client.connected_port else ""

                # Convention: ("Alice (12 min ago)", "Alice", 12593)
                clients.append((f"{client[1]}{me_notifier} ({time_passed})", (client[1], client[0][1])))

            # Emit clients fetched
            # Convention: ([("Alice (12 min ago)", "Alice", 12593)], [])
            self.updates_fetched.emit((clients, group_chat_rooms))

            # To put a fetching interval.
            time.sleep(1)

    def stop(self):
        """
        Stop the thread.
        """
        self.thread_alive = False
