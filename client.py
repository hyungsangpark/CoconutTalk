import select
import socket
import sys
import signal
import argparse


from PyQt5.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication(sys.argv)
    connection_widget = ConnectionWidget()
    sys.exit(app.exec_())
