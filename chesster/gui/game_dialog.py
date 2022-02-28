from PyQt5 import QtGui, QtSvg, QtWidgets, QtCore
from PyQt5.QtWidgets import QDialog, QLabel, QMessageBox, QGroupBox
from PyQt5.QtSvg import QSvgWidget, QGraphicsSvgItem
from chesster.gui.utils import get_ui_resource_path
from PyQt5.uic import loadUi
from chesster.Schach_KI.class_chess_gameplay import ChessGameplay
import PyQt5
# import os
# qt_path = os.path.dirname(PyQt5.__file__)
# os.environ['QT_PLUGIN_PATH'] = os.path.join(qt_path, "Qt/plugins")
from chesster.master.hypervisor import Hypervisor
import logging
import threading as th

logger = logging.getLogger(__name__)


class GameDialog(QDialog):
    def __init__(self, chess_engine_difficulty, player_color, FlagHints, NoHints, parent=None):
        super(GameDialog, self).__init__(parent)
        self.message_box = QMessageBox(self)
        self.message_box.windowTitleChanged.connect(self.show_notify)
        self.message_box_ending = QMessageBox(self)
        self.message_box_ending.windowTitleChanged.connect(self.show_notify_endgame)
        self.message_box_promotion = QMessageBox(self)
        self.message_box_promotion.windowTitleChanged.connect(self.show_notify_promotion)
        self.NoHints = NoHints
        self.FlagHints = FlagHints
        self.__counter = 0
        self.round = 0
        logger.info('Starting Game')
        ui_path = get_ui_resource_path('game_dialog.ui')
        loadUi(ui_path, self)
        self.Checkmate = False
        self.check_fail_flag = False
        self.game_state = "NoCheckmate"
        self.HintMove = ''
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
        self.hypervisor = Hypervisor(self.__robot_color, self.__player_color, chess_engine_difficulty)
        logger.info('Hypervisior initialized')
        logger.info('Starting hypervisor')
        self.hypervisor.start()
        logger.info('Hypervisor started')
        image = self.hypervisor.chess_engine.get_drawing('', True, self.__player_color)
        self.update_drawing(image)
        logger.info(f'Game Dialog Box started with difficulty: {chess_engine_difficulty} and player color: {player_color}')
        self.GameButton.clicked.connect(self.GameProcedureT)
        self.GameStatus_Text_Label.setText("Please place the chesspieces according to the Image. Press 'Start' to begin the game and wait for further instructions.")
        self.GameButton.setText('Start')
        self.Hint_Label_No.setText(f'{self.NoHints}')
        self.Hint_Label_Hint.setText('')
        self.HintButton.clicked.connect(self.Show_Hint)

        if self.FlagHints == False:
            logger.info('Hints deactivated. Hiding GUI Elements')
            self.Hint_Label_No.setHidden(True)
            self.Hint_Label_Hint.setHidden(True)
            self.HintButton.setHidden(True)
            self.Hint_Label_Text.setHidden(True)
        
    def turn_completed(self) -> None:
        """
        main procedure for the game. Only triggers when the human counterfeit finished its move and it's the robots turn
        """
        self.round +=1
        self.GameButton.setText('Move done')
        self.GameButton.setEnabled(False)
        if self.check_fail_flag:
            logger.info('Trying another detection attempt for last robot move...')
            self.check_fail_flag, image = self.hypervisor.recover_failure()
            if self.check_fail_flag:
                logger.info('Detection wrong again.')
                self.GameStatus_Text_Label.setText("Detection wrong again. Repeat instructions from before.")
                self.GameButton.setText('Try again')
                self.GameButton.setDisabled(False)
            else:
                logger.info('Detection successful.')
                self.GameStatus_Text_Label.setText("Detection successful! You may make your move now and press 'Move done' after you're finished.")
                self.GameButton.setDisabled(False)
                self.update_drawing(image)
        elif self.__counter==0: #Start of game
            if self.__robot_color == 'w': #Robot begins
                self.GameStatus_Text_Label.setText("Robot's move. Wait until the move ended and this instruction changes.")
                #self.hypervisor.robot.StartGesture(Beginner=True)
                actions, self.game_state, image, proof, failure_flag = self.hypervisor.analyze_game(start=True)
                self.game_state, image, failure_flag = self.hypervisor.make_move(actions)
                if failure_flag:
                    logger.info(f'Failure detected. Len of state: {self.hypervisor.detector.NoStateChanges}')
                    if self.hypervisor.detector.NoStateChanges == 1: #Failed to detect pieces properly
                        self.GameButton.setText('Corrected piece')
                        self.GameStatus_Text_Label.setText("Please correct the last moved piece and press 'Corrected Piece' for another attempt")
                        self.GameButton.setDisabled(False)
                        logger.info('opening notify window for failure_flag and len(state_change) = 1')
                        self.set_notify(f'The last move done by the robot could not be detected. Please move the last moved piece(ses) more to the center of their field', 'Detection Failure!', QMessageBox.Critical)
                    else: #Failed to detect pieces properly due to arm or sth like that in FOV
                        self.GameButton.setText('Try again')
                        self.GameStatus_Text_Label.setText("Please make sure that you don't put your hand in the field of view  of the camera after your move. Press 'Try again' to proceed.")
                        self.GameButton.setDisabled(False)
                        logger.info('opening notify window for failure_flag and len(state_change) > 4')
                        self.set_notify("It seems like you put your hand inside the field of view of the camera while scanning the field. Close this dialog and press 'Try again'", "Detection Failure!", QMessageBox.Critical)
                    self.check_fail_flag = failure_flag
                else:
                    self.update_drawing(image)
                    self.GameStatus_Text_Label.setText("Move done! It's Your turn. Press 'Move done' after you're finished.")
                    self.GameButton.setDisabled(False)
            else: #Human begins
                #self.hypervisor.robot.StartGesture(Beginner=False)
                self.GameStatus_Text_Label.setText("You begin. Press 'Move done' after you're finished.")
                self.GameButton.setDisabled(False)
                self.round-=1
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
                logger.info(f'Failure detected. Len of state: {self.hypervisor.detector.NoStateChanges}')
                if self.hypervisor.detector.NoStateChanges == 0: #Failed to detect pieces properly because no move was done by the player
                    self.GameButton.setText('Move done')
                    self.GameStatus_Text_Label.setText("You didn't move last time. Please make your move and press 'Move done'")
                    self.GameButton.setDisabled(False)
                    logger.info('opening notify window for failure_flag and len(state_change) = 0')
                    self.set_notify("It seems like you didn't make a move. Please make your move now and press 'Move done' on the main window.", "Try again", QMessageBox.Critical)

                elif self.hypervisor.detector.NoStateChanges == 1: #Failed to detect pieces properly
                    self.GameButton.setText('Corrected piece')
                    self.GameStatus_Text_Label.setText("Please correct the last moved piece and press 'Corrected Piece' for another attempt")
                    self.GameButton.setDisabled(False)
                    logger.info('opening notify window for failure_flag and len(state_change) = 1')
                    self.set_notify(f'The last move done by you could not be detected. Please move the last moved piece(ses) more to the center of their field', 'Detection Failure!', QMessageBox.Critical)
                
                else: #Failed to detect pieces properly due to an Arm or sth like that in FOV
                    self.GameButton.setText('Try again')
                    self.GameStatus_Text_Label.setText("Please make sure that you don't put your hand in the field of view  of the camera after your move. Press 'Try again' to proceed.")
                    self.GameButton.setDisabled(False)
                    logger.info('opening notify window for failure_flag and len(state_change) > 4')
                    self.set_notify("It seems like you put your hand inside the field of view of the camera while scanning the field. Close this dialog and press 'Try again'", "Detection Failure!", QMessageBox.Critical)

            else: #Standard case! regular game procedure
                self.update_drawing(image) #updated image after human move
                if self.game_state != "NoCheckmate": #Check if Human accomplished Checkmate
                    self.Checkmate = True
                    self.end_game(self.game_state)
                    
                else: #Moves pieces
                    self.game_state, image, failure_flag = self.hypervisor.make_move(actions) #make moves received on analyze_game
                    if failure_flag:
                        logger.info(f'Failure detected. Len of state: {self.hypervisor.detector.NoStateChanges}')
                        if self.hypervisor.detector.NoStateChanges == 1: #Failed to detect pieces properly
                            self.GameButton.setText('Corrected piece')
                            self.GameStatus_Text_Label.setText("Please correct the last moved piece and press 'Corrected Piece' for another attempt")
                            self.GameButton.setDisabled(False)
                            logger.info('opening notify window for failure_flag and len(state_change) = 1')
                            self.set_notify(f'The last move done by the robot could not be detected. Please move the last moved piece(ses) more to the center of their field', 'Detection Failure!', QMessageBox.Critical)
                        else: #Failed to detect pieces properly due to arm or sth like that in FOV
                            self.GameButton.setText('Try again')
                            self.GameStatus_Text_Label.setText("Please make sure that you don't put your hand in the field of view  of the camera after your move. Press 'Try again' to proceed.")
                            self.GameButton.setDisabled(False)
                            logger.info('opening notify window for failure_flag and len(state_change) > 4')
                            self.set_notify("It seems like you put your hand inside the field of view of the camera while scanning the field. Close this dialog and press 'Try again'", "Detection Failure!", QMessageBox.Critical)
                        self.check_fail_flag = failure_flag #to initialize recover_failure() the next time the button is pressed. Only neccesary at robot move level because at player move level, nothing changed and the procedure can just be repeated
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
        super(GameDialog, self).close()

    def update_drawing(self, svg_image):
        logger.info('Updating drawing...')
        svg_image = bytes(svg_image, 'utf8')
        self.svg_widget.renderer().load(svg_image)
        self.svg_widget.show()
        logger.info('Updating drawing completed.')

    def set_notify(self, message, title='message', icon=QMessageBox.Warning):
        #self.message_box.setIcon(icon)
        self.message_box.setText(message)   
        self.message_box.setWindowTitle(title)
        
    def show_notify(self):
        self.message_box.exec()
        self.message_box = QMessageBox(self)
        self.message_box.windowTitleChanged.connect(self.show_notify)

    def set_notify_endgame(self, message, title='message'):
        self.message_box_ending.setText(message)
        #self.message_box_ending.setIcon(QMessageBox.Information)
        self.message_box_ending.setWindowTitle(title)
        
    def show_notify_endgame(self):
        self.message_box_ending.exec()
        self.closeEvent(False)

    def set_notify_promotion(self):
        self.message_box_promotion.setText("You promoted a pawn. Please select the piece you swapped the pawn for.")   
        self.QueenB = self.message_box_promotion.addButton('Queen', QMessageBox.NoRole)
        self.KnightB = self.message_box_promotion.addButton('Knight', QMessageBox.NoRole)
        self.message_box_promotion.setWindowTitle('Promotion!')

    def show_notify_promotion(self):
        self.message_box_promotion.exec()
        if self.message_box_promotion.clickedButton() == self.QueenB:
            if self.__player_color == 'w':
                self.hypervisor.detector.board.last_promotionfield.state = 'Q'
            else:
                self.hypervisor.detector.board.last_promotionfield.state = 'q'
        elif self.message_box_promotion.clickedButton() == self.KnightB:
            if self.__player_color == 'w':
                self.hypervisor.detector.board.last_promotionfield.state = 'K'
            else:
                self.hypervisor.detector.board.last_promotionfield.state = 'k'
        self.message_box_promotion = QMessageBox(self)
        self.message_box_promotion.windowTitleChanged.connect(self.show_notify)

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

    def Check_Promote(self):
        if self.hypervisor.detector.board.promoting == True:
            logger.info('Promotion detected. Displaying window to get which promotion occured.')

    def Show_Hint(self):
        logger.info('Showing Hint')
        if self.round == 0:
            self.Hint_Label_Hint.setText("It's your turn to start. Please make your first move before you can use hints.")
        elif self.NoHints == 0:
            self.Hint_Label_Hint.setText("Sorry, you used all your available hints! It's only (wo)man versus machine now!")
        else:
            logger.info('Getting Hint from AI')
            self.HintMove = self.hypervisor.chess_engine.engine.get_best_move()
            logger.info('Hint: ' + self.HintMove)
            self.Hint_Label_Hint.setText('Tip from the AI: ' + self.HintMove)
            self.NoHints-=1
            self.Hint_Label_No.setText(f'{self.NoHints}')
            image = self.hypervisor.chess_engine.get_drawing(self.HintMove, True, self.__player_color, hint=True)
            self.update_drawing(image)
