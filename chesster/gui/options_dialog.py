from PyQt5.QtWidgets import QDialog
from PyQt5.uic import loadUi
from chesster.gui.utils import get_ui_resource_path
from chesster.gui.chess_rules_resources import *


class ChessOptions(QDialog):
    def __init__(self, parent=None):
        super(ChessOptions, self).__init__(parent)
        ui_path = get_ui_resource_path('options.ui')
        loadUi(ui_path, self)
