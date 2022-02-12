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
        self.__counter=0
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
        self.hypervisor = Hypervisor(logger,self.notify, self.__robot_color, self.__player_color, chess_engine_difficulty)
        logger.info('Hypervisior initialized')
        logger.info('Starting hypervisor')
        self.hypervisor.start()
        logger.info('Hypervisor started')
        image = self.hypervisor.chess_engine.get_drawing()
        self.update_drawing(image)
        logger.info(f'Game Dialog Box started with difficulty: {chess_engine_difficulty} and player color: {player_color}')
        self.actionAccept.triggered.connect(self.turn_completed)
        self.GameStatus_Text_Label.setText("Press 'Start' to begin the game and wait for further instructions.")
        self.actionAccept.setText('Start')
        self.actionCancle.setText('Abort')
    
    def turn_completed(self) -> None:
        """
        main procedure for the game
        """
        self.actionAccept.setText('Move done')
        self.actionAccept.setEnabled(False)
        if self.__counter==0:
            if self.__robot_color == 'w':
                self.GameStatus_Text_Label.setText("Robot's move. Wait until the move ended and this instruction changes.")
                self.hypervisor.robot.StartGesture(Beginner=True)
                self.game_state, image, proof = self.hypervisor.make_move(start=True)
                self.update_drawing(image)
                self.GameStatus_Text_Label.setText("Move done! It's Your turn. Press 'Move done' after you're finished.")
                self.actionAccept.setDisabled(False)
            else:
                self.hypervisor.robot.StartGesture(Beginner=False)
                self.GameStatus_Text_Label.setText("You begin. Press 'Move done' after you're finished.")
                self.actionAccept.setDisabled(False)
            self.__counter=self.__counter+1
        else:
            logger.info('Player\'s turn confirmed')
            self.GameStatus_Text_Label.setText("Robot's move. Wait until the move ended and this instruction changes.")
            self.game_state, image, proof = self.hypervisor.make_move(start=False)
            if proof == False:
                self.actionAccept.setText('Move changed')
                self.notify(f'your recent move {self.hypervisor.last_move_human} was accounted as wrong. Please change your move.', 'Proof Violation')
                self.GameStatus_Text_Label.setText("Please press 'Move changed' after you have corrected your move.")
                self.actionAccept.setDisabled(False)
            else:
                self.update_drawing(image)
                self.GameStatus_Text_Label.setText("Move done! It's Your turn again. Press 'Move done' after you're finished.")
                self.actionAccept.setDisabled(False)

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
            self.notify('You loose! Robot Won! GG. Close this dialog to return to the main menu.', 'Checkmate!')
        else:
            self.hypervisor.robot.EndGesture(Victory=False)
            self.notify('You Won! Robot loose! GG. Close this dialog to return to the main menu.', 'Checkmate!')
        self.closeEvent()
