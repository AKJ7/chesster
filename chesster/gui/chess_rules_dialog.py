from PyQt5.QtWidgets import QDialog
from PyQt5.uic import loadUi
import os


class ChessRulesDialog(QDialog):
    # Site: https://www.wiki-schacharena.de/Schachregeln_f%C3%BCr_Einsteiger
    def __init__(self, parent=None):
        super(ChessRulesDialog, self).__init__(parent)
        file_path = f'{os.getcwd()}/gui/chess_rules_dialog.ui'
        loadUi(file_path, self)
