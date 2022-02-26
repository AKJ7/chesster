from PyQt5.QtWidgets import QDialog, QLabel, QGroupBox, QRadioButton
from PyQt5.uic import loadUi
from PyQt5.QtGui import QTextDocument
# from chesster.gui.game_dialog import GameDialog
from chesster.gui.game_dialog_dual import GameDialog #New
import random
from chesster.gui.utils import get_ui_resource_path, SUPPORTED_CHESS_COLORS


class StartDialog(QDialog):
    def __init__(self, parent=None):
        super(StartDialog, self).__init__(parent)
        #ui_path = get_ui_resource_path('start_dialog.ui')
        ui_path = get_ui_resource_path('start_dialog_midgameadd.ui')
        loadUi(ui_path, self)
        self.parent = parent
        self.actionAccept.triggered.connect(self.on_accept)
        self.horizontalSlider.valueChanged.connect(self.update_hints)
        self.checkBox_hints.toggled.connect(self.update_hints)
        self.label_number_hints.setText('/')
        self.Radio_Elo.toggled.connect(self.update_difficulty)
        self.Radio_Difficulty.toggled.connect(self.update_difficulty)
        self.NoHints = 0

    def on_accept(self) -> None:
        doc = QTextDocument()
        doc.setHtml(self.label.text())
        chess_engine_difficulty = doc.toPlainText()
        player_color = 'w'
        FlagHints = self.checkBox_hints.isChecked()
        FlagMidgame = self.checkBox_midgame.isChecked() #New
        for radio_button in self.groupBox.findChildren(QRadioButton):
            if radio_button.isChecked():
                color_name = radio_button.text().lower()
                if color_name in SUPPORTED_CHESS_COLORS.keys():
                    player_color = SUPPORTED_CHESS_COLORS[color_name][0].lower()
                else:
                    player_color = random.choice(['w', 'b'])
                break
        self.close()
        #game_dialog = GameDialog(chess_engine_difficulty, player_color, FlagHints, self.NoHints, parent=self.parent)
        game_dialog = GameDialog(chess_engine_difficulty, player_color, FlagHints, self.NoHints, FlagMidgame, parent=self.parent) #New
        game_dialog.show()

    def update_hints(self):
        if self.checkBox_hints.isChecked():
            Difficulty = int(self.horizontalSlider.value())
            DiffSteps = [5, 10, 15]
            EloSteps = [1000, 2000, 3000]

            if self.Radio_Elo.isChecked():
                Steps = EloSteps
            else:
                Steps = DiffSteps

            if Difficulty <= Steps[0]:
                self.NoHints = 4
            elif Difficulty <= Steps[1]:
                self.NoHints = 3
            elif Difficulty <= Steps[2]:
                self.NoHints = 2
            else:
                self.NoHints = 1
            self.label_number_hints.setText(f'{self.NoHints}')
        else:
            self.label_number_hints.setText('/')
            
    def update_difficulty(self):
        if self.Radio_Elo.isChecked():
            self.groupBox_2.setTitle('Elo Rating [x-Y]')
            self.horizontalSlider.setMinimum(0)
            self.horizontalSlider.setMaximum(4000)
            self.horizontalSlider.setValue(2000)
        else:
            self.groupBox_2.setTitle('Difficulty [1-20]')
            self.horizontalSlider.setMinimum(1)
            self.horizontalSlider.setMaximum(20)
            self.horizontalSlider.setValue(3)
