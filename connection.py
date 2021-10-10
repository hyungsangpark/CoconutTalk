from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QGridLayout, QLineEdit


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
        print(f"IP Address: {self.ip_address_line_edit.text()}")
        print(f"Port: {self.port_line_edit.text()}")
        print(f"Nickname: {self.nickname_line_edit.text()}")
