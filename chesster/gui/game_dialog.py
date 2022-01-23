from PyQt5 import QtGui, QtSvg, QtWidgets, QtCore
from PyQt5.QtWidgets import QDialog, QLabel, QMessageBox
from PyQt5.QtGui import QColor, QFont, QImage, QPainter, QPainterPath, QPixmap
from PyQt5.QtSvg import QSvgWidget, QGraphicsSvgItem
#from chesster import Schach_KI
#from chesster.Schach_KI.main import VBC_command
from chesster.gui.utils import get_ui_resource_path
from PyQt5.uic import loadUi
from chesster.chess_engine.chess_engine import ChessEngine
from chesster.Schach_KI.class_chess_gameplay import ChessGameplay
import logging
logger = logging.getLogger(__name__)


class GameDialog(QDialog):
    def __init__(self, chess_engine_difficulty, player_color, parent=None):
        super(GameDialog, self).__init__(parent)
        ui_path = get_ui_resource_path('game_dialog.ui')
        loadUi(ui_path, self)
        self.__player_color = player_color
        self.svg_widget = QSvgWidget()
        self.svg_widget.sizeHint()
        self.svg_widget.setMinimumSize(512, 512)
        self.svg_widget.adjustSize()
        self.gridLayout.addWidget(self.svg_widget)
        self.engine = ChessGameplay(chess_engine_difficulty)
        image = self.engine.get_drawing()
        self.update_drawing(image)
        logger.info(f'Game Dialog Box started with difficulty: {chess_engine_difficulty} and player color: {player_color}')
        #self.engine.play()
        image = self.engine.get_drawing()
        self.update_drawing(image)
        self.actionAccept.triggered.connect(self.turn_completed)

    def turn_completed(self) -> None:
        logger.info('Player\'s turn confirmed')
        Move, CheckMate_KI, CheckMate_Player, _ = self.engine.play_ki([], self.__player_color)
        image = self.engine.get_drawing()
        self.update_drawing(image)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        logger.info('Closing')
        self.engine.stop()
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
