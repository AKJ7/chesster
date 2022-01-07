from PyQt5.QtWidgets import QDialog
from PyQt5.uic import loadUi
from chesster.gui.utils import get_ui_resource_path
from chesster.gui.chess_rules_resources import *


class ChessRulesDialog(QDialog):
    def __init__(self, parent=None):
        super(ChessRulesDialog, self).__init__(parent)
        ui_path = get_ui_resource_path('chess_rules_dialog.ui')
        loadUi(ui_path, self)
