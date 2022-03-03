from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QDialog, QRadioButton, QPushButton
from PyQt5.QtCore import QSettings
from chesster.gui.utils import get_ui_resource_path, CHESS_PIECE_MAP
from chesster.master.game_state import PieceColor
import logging
import chess
from chess.svg import piece
from PyQt5.QtSvg import QSvgWidget, QSvgRenderer
from PyQt5.QtGui import QPainter, QPixmap, QIcon
from PyQt5 import QtCore

logger = logging.getLogger(__name__)


class PromotionDialog(QDialog):
    def __init__(self, player_color=PieceColor.BLACK, parent=None):
        super(PromotionDialog, self).__init__(parent)
        ui_path = get_ui_resource_path('promotion_dialog.ui')
        loadUi(ui_path, self)
        self.pixel_map = None
        self.player_color = player_color
        self.selected_piece = 'bauer'
        for button in self.groupBox.findChildren(QPushButton):
            button_text = button.text().lower()
            piece_symbol = CHESS_PIECE_MAP[button_text]
            icon = self.__get_icon_from_svg(piece_symbol if player_color == PieceColor.BLACK else piece_symbol.upper())
            button.setIcon(icon)

    def accept(self) -> None:
        logger.info('Accepted')
        for button in self.groupBox.findChildren(QPushButton):
            button_text = button.text().lower()
            if button.isChecked():
                self.selected_piece = button_text
                break
        super(PromotionDialog, self).accept()

    def prompt_user_promotion_piece(self) -> str:
        self.exec()
        translated_color = CHESS_PIECE_MAP[self.selected_piece]
        logger.info(f'User selection - color: {self.player_color}, translated_color: {translated_color}')
        return translated_color if self.player_color == PieceColor.BLACK else translated_color.upper()

    def __get_icon_from_svg(self, symbol: str) -> QIcon:
        svg_icon = piece(chess.Piece.from_symbol(symbol))
        svg_renderer = QSvgRenderer()
        svg_renderer.load(bytes(svg_icon, 'utf8'))
        self.pixel_map = QPixmap(svg_renderer.defaultSize())
        self.pixel_map.fill(QtCore.Qt.transparent)
        painter = QPainter(self.pixel_map)
        svg_renderer.render(painter)
        return QIcon(self.pixel_map)
