from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QDialog, QRadioButton
from PyQt5.QtCore import QSettings
import logging
from chesster.gui.utils import get_ui_resource_path, CHESS_PIECE_MAP

logger = logging.getLogger(__name__)


class PromotionDialog(QDialog):
    def __init__(self, parent=None):
        super(PromotionDialog, self).__init__(parent)
        ui_path = get_ui_resource_path('promotion_dialog.ui')
        loadUi(ui_path, self)
        self.selected_piece = None

    def accept(self) -> None:
        logger.info('Accepted')
        for radio_button in self.groupBox.findChildren(QRadioButton):
            if radio_button.isChecked():
                self.selected_piece = radio_button.text().lower()
        super(PromotionDialog, self).accept()

    def prompt_user_promotion_piece(self, user_color='b') -> str:
        self.exec()
        translated_color = CHESS_PIECE_MAP[self.selected_piece]
        logger.info(f'User selection - color: {user_color}, translated_color: {translated_color}')
        return translated_color if user_color == 'b' else translated_color.upper()
