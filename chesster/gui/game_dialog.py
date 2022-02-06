from PyQt5 import QtGui, QtSvg, QtWidgets, QtCore
from PyQt5.QtWidgets import QDialog, QLabel, QMessageBox
from PyQt5.QtGui import QColor, QFont, QImage, QPainter, QPainterPath, QPixmap
from PyQt5.QtSvg import QSvgWidget, QGraphicsSvgItem
from sklearn.ensemble import VotingClassifier
#from chesster import Schach_KI
#from chesster.Schach_KI.main import VBC_command
from chesster.gui.utils import get_ui_resource_path
from PyQt5.uic import loadUi
from chesster.chess_engine.chess_engine import ChessEngine
from chesster.Schach_KI.class_chess_gameplay import ChessGameplay
from chesster.master.hypervisor import Hypervisor
import logging
logger = logging.getLogger(__name__)


class GameDialog(QDialog):
    def __init__(self, chess_engine_difficulty, player_color, parent=None):
        super(GameDialog, self).__init__(parent)
        logger.info('Starting Game')
        ui_path = get_ui_resource_path('game_dialog.ui')
        loadUi(ui_path, self)
        self.Checkmate=False
        self.game_state="NoCheckmate"
        self.__player_color = player_color
        logger.info('Setting player colors')
        if self.__player_color == 'w':
            logger.info('Human: White | Robot: Black')
            self.__robot_color = 'b'
        else:
            logger.info('Human: Black | Robot: White')
            self.__robot_color = 'w'
        self.svg_widget = QSvgWidget()
        self.svg_widget.sizeHint()
        self.svg_widget.setMinimumSize(512, 512)
        self.svg_widget.adjustSize()
        self.gridLayout.addWidget(self.svg_widget)
        logger.info('initializing hypervisor')
        self.hypervisor = Hypervisor("/",self.notify, self.__robot_color, self.__player_color) #TBD
        logger.info('Hypervisior initialized')
        logger.info('Starting hypervisor')
        self.hypervisor.start()
        logger.info('Hypervisor started')
        image = self.hypervisor.chess_engine.get_drawing()
        self.update_drawing(image)
        logger.info(f'Game Dialog Box started with difficulty: {chess_engine_difficulty} and player color: {player_color}')
        self.actionAccept.triggered.connect(self.turn_completed)

        if self.__robot_color == 'w':
            self.hypervisor.robot.StartGesture(Beginner=True)
            self.game_state = self.hypervisor.make_move(start=True)
            image = self.hypervisor.chess_engine.get_drawing()
            self.update_drawing(image)
        else:
            self.hypervisor.robot.StartGesture(Beginner=False)
    
    def turn_completed(self) -> None:
        """
        main procedure for the game
        """
        logger.info('Player\'s turn confirmed')
        self.game_state = self.hypervisor.make_move(start=False)
        image = self.hypervisor.make_move(start=False)
        self.update_drawing(image)

        if self.game_state != "NoCheckmate":
            self.Checkmate = True
            self.end_game(self.game_state)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        logger.info('Closing')
        self.hypervisor.stop()
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

    def end_game(self, state):
        """
        End of the game procedure with Endgestures and space for messages
        """
        if state=="RobotVictory":
            self.hypervisor.robot.EndGesture(Victory=True)
        else:
            self.hypervisor.robot.EndGesture(Victory=False)

        self.closeEvent()
