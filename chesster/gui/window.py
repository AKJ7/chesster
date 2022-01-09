import sys
import signal
import logging
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow, QMessageBox
from PyQt5.uic import loadUi
from chesster.gui.window_ui import Ui_MainWindow
from chesster.gui.chess_rules_dialog import ChessRulesDialog
from chesster.gui.start_dialog import StartDialog
from chesster.gui.options_dialog import ChessOptions

logger = logging.getLogger(__name__)


class Window(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        logger.info('Starting GUI')
        super(Window, self).__init__(parent)
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        self.setupUi(self)
        self.connect_signal_slots()

    def connect_signal_slots(self):
        self.actionExit.triggered.connect(self.close)
        self.actionAbout.triggered.connect(self.about)
        self.actionChessRules.triggered.connect(self.chess_rules)
        self.actionStart.triggered.connect(self.start_dialog)
        self.actionOptions.triggered.connect(self.options_dialog)

    def about(self):
        QMessageBox.about(self, 'About CHESSter',
                          '<p>An AI robot chess project</p>'
                          '<p>@2022</p>')

    def chess_rules(self):
        dialog = ChessRulesDialog(self)
        dialog.exec()

    def options_dialog(self):
        dialog = ChessOptions(self)
        dialog.exec()

    def start_dialog(self):
        dialog = StartDialog(self)
        dialog.exec()

    @staticmethod
    def interrupt_exit(signal_value: int):
        logger.log(f'Interrupt Exit: {signal}')
        exit(signal_value)

