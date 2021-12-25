from PyQt5.QtWidgets import QDialog, QLabel, QGroupBox, QRadioButton
from PyQt5.uic import loadUi
import os
from PyQt5.QtGui import QTextDocument
from chesster.gui.game_dialog import GameDialog
import random


class StartDialog(QDialog):
    def __init__(self, parent=None):
        super(StartDialog, self).__init__(parent)
        file_path = f'{os.getcwd()}/gui/start_dialog.ui'
        loadUi(file_path, self)

    def accept(self) -> None:
        doc = QTextDocument()
        doc.setHtml(self.label.text())
        chess_engine_difficulty = doc.toPlainText()
        player_color = 'w'
        for radio_button in self.groupBox.findChildren(QRadioButton):
            if radio_button.isChecked():
                if radio_button.text() in ['Weiß', 'Schwarz']:
                    player_color = radio_button.text()[0].lower()
                else:
                    player_color = random.choice(['w', 'b'])
                break
        self.close()
        game_dialog = GameDialog(chess_engine_difficulty, player_color)
        game_dialog.exec()
