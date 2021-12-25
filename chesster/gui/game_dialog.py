from PyQt5 import QtGui, QtSvg, QtWidgets, QtCore
from PyQt5.QtWidgets import QDialog, QLabel, QMessageBox
from PyQt5.QtGui import QColor, QFont, QImage, QPainter, QPainterPath, QPixmap
from PyQt5.QtSvg import QSvgWidget, QGraphicsSvgItem
import os
from PyQt5.uic import loadUi
from chesster.chess_engine.chess_engine import ChessEngine
import logging


logger = logging.getLogger(__name__)


class GameDialog(QDialog):
    def __init__(self, chess_engine_difficulty, player_color, parent=None):
        super(GameDialog, self).__init__(parent)
        file_path = f'{os.getcwd()}/gui/game_dialog.ui'
        loadUi(file_path, self)
        self.engine = ChessEngine()
        self.svg_widget = QSvgWidget()
        self.svg_widget.setFixedSize(512, 512)
        self.gridLayout.addWidget(self.svg_widget)
        image = self.engine.get_drawing()
        self.update_drawing(image)
        logger.info(f'Game Dialog Box started with difficulty: {chess_engine_difficulty} and player color: {player_color}')
        self.engine.play()
        image = self.engine.get_drawing()
        self.update_drawing(image)
        # Insert further game logic here.

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        logger.info('Closing')
        super(GameDialog, self).closeEvent(a0)

    def update_drawing(self, svg_image):
        svg_image = bytes(svg_image, 'utf8')
        self.svg_widget.renderer().load(svg_image)
        self.svg_widget.show()

    def notify(self, message, title='message'):
        message_box = QMessageBox(self)
        message_box.setWindowTitle(title)
        message_box.setText(message)
        message_box.exec()
