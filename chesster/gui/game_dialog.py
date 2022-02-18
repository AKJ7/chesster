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
import threading as th
import time
import numpy as np
logger = logging.getLogger(__name__)


class GameDialog(QDialog):
    def __init__(self, chess_engine_difficulty, player_color, parent=None):
        super(GameDialog, self).__init__(parent)
        self.message_box = QMessageBox(self)
        self.message_box.windowTitleChanged.connect(self.show_notify)
        self.message_box_ending = QMessageBox(self)
        self.message_box_ending.windowTitleChanged.connect(self.show_notify_endgame)
        self.__counter=0
        logger.info('Starting Game')
        ui_path = get_ui_resource_path('game_dialog.ui')
        loadUi(ui_path, self)
        self.Checkmate=False
        self.check_fail_flag = False
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
        image = self.hypervisor.chess_engine.get_drawing('', True, self.__player_color)
        self.update_drawing(image)
        logger.info(f'Game Dialog Box started with difficulty: {chess_engine_difficulty} and player color: {player_color}')
        self.GameButton.clicked.connect(self.GameProcedureT)
        self.GameButton.setGeometry(11, 528, 793, 50)
        self.GameStatus_Text_Label.setText("Please place the chesspieces according to the Image. Press 'Start' to begin the game and wait for further instructions.")
        self.GameButton.setText('Start')
        
    def turn_completed(self) -> None:
        """
        main procedure for the game. Only triggers when the human counterfeit finished its move and it's the robots turn
        """
        self.GameButton.setText('Move done')
        self.GameButton.setEnabled(False)
        if self.check_fail_flag:
            logger.info('Trying another detection attempt for last robot move...')
            self._check_fail_flag, image = self.hypervisor.recover_failure()
            if self._check_fail_flag:
                self.GameStatus_Text_Label.setText("Detection wrong again. Move piece again.")
                self.GameButton.setText('Corrected piece')
                self.GameButton.setDisabled(False)
            else:
                self.GameStatus_Text_Label.setText("Detection successful! You may make your move now and press 'Move Done' after you're finished.")
                self.GameButton.setDisabled(False)
                self.update_drawing(image)
        elif self.__counter==0: #Start of game
            if self.__robot_color == 'w': #Robot begins
                self.GameStatus_Text_Label.setText("Robot's move. Wait until the move ended and this instruction changes.")
                self.hypervisor.robot.StartGesture(Beginner=True)
                actions, self.game_state, image, proof, failure_flag = self.hypervisor.analyze_game(start=True)
                self.game_state, image, failure_flag = self.hypervisor.make_move(actions)
                if failure_flag:
                    self.GameButton.setText('Corrected piece')
                    self.GameStatus_Text_Label.setText("Please correct the last moved piece and press 'Corrected Piece' for another attempt")
                    self.GameButton.setDisabled(False)
                    logger.info('opening notify window for failure_flag')
                    self.check_fail_flag = failure_flag
                    self.set_notify(f'The last move done by the robot could not be detected. Please move the last moved piece(ses) more to the center of the field', 'Detection Failure!')
                else:
                    self.update_drawing(image)
                    self.GameStatus_Text_Label.setText("Move done! It's Your turn. Press 'Move done' after you're finished.")
                    self.GameButton.setDisabled(False)
            else: #Human begins
                logger.info('Test')
                self.hypervisor.robot.StartGesture(Beginner=False)
                self.GameStatus_Text_Label.setText("You begin. Press 'Move done' after you're finished.")
                self.GameButton.setDisabled(False)
            self.__counter=self.__counter+1

        else: #regular game procedure -> Robot move
            logger.info('Player\'s turn confirmed')
            self.GameStatus_Text_Label.setText("Robot's move. Wait until the move ended and this instruction changes.")
            actions, self.game_state, image, proof, failure_flag = self.hypervisor.analyze_game(start=False) #First analyze changes and determine proof violation
            if proof == False: #==False = proof violation -> Wrong move detected, if regular move=Robot already rolled back the move
                self.GameButton.setText('Move changed')
                self.GameStatus_Text_Label.setText("Please press 'Move changed' after you have corrected your move.")
                self.GameButton.setDisabled(False)
                self.update_drawing(image) #updated image after human move
                logger.info('opening notify window')
                self.set_notify(f'your recent move {self.hypervisor.last_move_human} was accounted as wrong. Please change your move.', 'Proof Violation')
            elif failure_flag:
                self.GameButton.setText('Corrected piece')
                self.GameStatus_Text_Label.setText("Please correct the last moved piece and press 'Corrected Piece' for another attempt")
                self.GameButton.setDisabled(False)
                logger.info('opening notify window for failure_flag')
                self.set_notify(f'The last move done by you could not be detected. Please move the last moved piece(ses) more to the center of the field', 'Detection Failure!')
            else: #Standard case! regular game procedure
                self.update_drawing(image) #updated image after human move
                if self.game_state != "NoCheckmate": #Check if Human accomplished Checkmate
                    self.Checkmate = True
                    self.end_game(self.game_state)
                    
                else: #Moves pieces
                    self.game_state, image, failure_flag = self.hypervisor.make_move(actions) #make moves received on analyze_game
                    if failure_flag:
                        self.GameButton.setText('Corrected piece')
                        self.GameStatus_Text_Label.setText("Please correct the last moved piece and press 'Corrected Piece' for another attempt")
                        self.GameButton.setDisabled(False)
                        logger.info('opening notify window for failure_flag')
                        self.set_notify(f'The last move done by the robot could not be detected. Please move the last moved piece(ses) more to the center of the field', 'Detection Failure!')
                        self.check_fail_flag = failure_flag
                    else:
                        self.update_drawing(image) #updated image after robot move
                        self.GameStatus_Text_Label.setText("Move done! It's Your turn again. Press 'Move done' after you're finished.")
                        self.GameButton.setDisabled(False)

                        if self.game_state != "NoCheckmate": #Check if Robot accomplished Checkmate
                            self.Checkmate = True
                            self.end_game(self.game_state)

    def GameProcedureT(self):
        Thread = th.Thread(target=self.turn_completed)
        Thread.start()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        logger.info('Closing')
        self.hypervisor.stop()
        super(GameDialog, self).closeEvent(a0)

    def update_drawing(self, svg_image):
        logger.info('Updating drawing...')
        svg_image = bytes(svg_image, 'utf8')
        self.svg_widget.renderer().load(svg_image)
        self.svg_widget.show()
        logger.info('Updating drawing completed.')

    def set_notify(self, message, title='message'):
        self.message_box.setText(message)   
        self.message_box.setWindowTitle(title)
        
    def show_notify(self):
        self.message_box.exec()
        self.message_box = QMessageBox(self)
        self.message_box.windowTitleChanged.connect(self.show_notify)

    def set_notify_endgame(self, message, title='message'):
        self.message_box_ending.setText(message)
        self.message_box_ending.setWindowTitle(title)
        
    def show_notify_endgame(self):
        self.message_box_ending.exec()
        self.closeEvent(False)

    def end_game(self, state):
        """
        End of the game procedure with Endgestures and space for messages
        """
        if state=="RobotVictory":
            self.set_notify_endgame('You loose! Robot Won! GG. Close this dialog to return to the main menu.', 'Checkmate!')
            self.hypervisor.robot.EndGesture(Victory=True)
        else:
            self.set_notify_endgame('You Won! Robot loose! GG. Close this dialog to return to the main menu.', 'Checkmate!')
            self.hypervisor.robot.EndGesture(Victory=False)
