from PyQt5.QtWidgets import QDialog, QLabel, QGroupBox, QRadioButton
from PyQt5.uic import loadUi
from PyQt5.QtGui import QTextDocument
#from chesster.gui.game_dialog import GameDialog
from chesster.gui.game_dialog_dual import GameDialog #New
from chesster.master.game_state import PieceColor
import random
from chesster.gui.utils import get_ui_resource_path, SUPPORTED_CHESS_COLORS
import logging
from chesster.gui.promotion_dialog import PromotionDialog

logger = logging.getLogger(__name__)


class StartDialog(QDialog):
    def __init__(self, parent=None):
        super(StartDialog, self).__init__(parent)
        ui_path = get_ui_resource_path('start_dialog_midgameadd.ui')
        loadUi(ui_path, self)
        self.parent = parent
        self.actionAccept.triggered.connect(self.on_accept)
        self.horizontalSlider.valueChanged.connect(self.update_hints)
        self.checkBox_hints.toggled.connect(self.update_hints)
        self.label_number_hints.setText('0')
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
        # promotion_dialog = PromotionDialog(player_color=PieceColor.BLACK, parent=self.parent)
        # selected_piece = promotion_dialog.prompt_user_promotion_piece()
        # logger.info(f'User selected piece: {selected_piece}')
        # game_dialog = GameDialog(chess_engine_difficulty, player_color, FlagHints, self.NoHints, parent=self.parent)
        game_dialog = GameDialog(chess_engine_difficulty, player_color, FlagHints, self.NoHints, FlagMidgame, parent=self.parent) #New
        game_dialog.show()

    def update_hints(self):
        if self.checkBox_hints.isChecked():
            difficulty = int(self.horizontalSlider.value())
            difficulty_steps = (5, 10, 15)
            if difficulty <= difficulty_steps[0]:
                self.NoHints = 4
            elif difficulty <= difficulty_steps[1]:
                self.NoHints = 3
            elif difficulty <= difficulty_steps[2]:
                self.NoHints = 2
            else:
                self.NoHints = 1
            self.label_number_hints.setText(f'{self.NoHints}')
        else:
            self.label_number_hints.setText('0')
