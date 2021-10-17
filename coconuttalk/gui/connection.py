import socket

from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QWidget, QLineEdit, QVBoxLayout, QGridLayout, QLabel, QHBoxLayout, QPushButton, QMessageBox

from coconuttalk.chat.chat_client import ChatClient
from coconuttalk.gui.connected import ConnectedWidget


class ConnectionWidget(QWidget):
    """
    A PyQT5 widget for connection screen.
    """

    def __init__(self):
        super().__init__()
        self.ip_address_line_edit = QLineEdit()
        self.ip_address_line_edit.setPlaceholderText("localhost")
        self.port_line_edit = QLineEdit()
        self.port_line_edit.setPlaceholderText("9988")
        self.nickname_line_edit = QLineEdit()
        self.init_ui()

    def init_ui(self) -> None:
        """
        Initializes the UI of the program and displays it.
        """

        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        main_layout.addStretch(1)

        # input_grid layout
        input_grid = QGridLayout()

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

        # Add input_grid to main_layout.
        main_layout.addLayout(input_grid)

        # Add spacer between input section and buttons section.
        main_layout.addStretch(1)

        # buttons_h_box layout
        buttons_h_box = QHBoxLayout()

        # Spacer on left side of the buttons HBox.
        buttons_h_box.addStretch()

        connect_button = QPushButton("Connect", self)
        connect_button.clicked.connect(self.connect)
        connect_button.setAutoDefault(True)
        buttons_h_box.addWidget(connect_button)

        cancel_button = QPushButton("Cancel", self)
        cancel_button.clicked.connect(QCoreApplication.instance().quit)
        buttons_h_box.addWidget(cancel_button)

        # Add buttons_h_box to main_layout.
        main_layout.addLayout(buttons_h_box)

        # Set window properties of this widget application and show it.
        self.setWindowTitle("CoconutTalk")
        self.setGeometry(300, 300, 300, 200)
        self.show()

    def connect(self) -> None:
        """
        Connects the client to the server with the given input field values.
        This is a Connect button on-click handler.
        """
        ip_address = "localhost" if self.ip_address_line_edit.text() == "" else self.ip_address_line_edit.text()
        port: int = int(9988 if self.port_line_edit.text() == "" else self.port_line_edit.text())
        nickname = self.nickname_line_edit.text()

        if nickname == "":
            notify_non_empty_nickname = QMessageBox()
            notify_non_empty_nickname.setText("Please enter a non-empty nickname")
            notify_non_empty_nickname.exec()
            return

        print(f"IP Address: {ip_address}")
        print(f"Port: {port}")
        print(f"Nickname: {nickname}")

        try:
            client = ChatClient(nickname=nickname, host=ip_address, port=port)
            self.connected_widget = ConnectedWidget(client)
            self.connected_widget.show()
            self.close()
        except socket.error:
            notify_exit = QMessageBox()
            notify_exit.setText("Server could not be found!")
            notify_exit.setInformativeText(
                "Please start the server before the client, or change the server port and address.")
            notify_exit.exec()
