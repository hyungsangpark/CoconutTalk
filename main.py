import sys

from PyQt5.QtWidgets import QApplication

from coconuttalk.gui.connection import ConnectionWidget

if __name__ == '__main__':
    app = QApplication(sys.argv)
    connection_widget = ConnectionWidget()
    sys.exit(app.exec_())
