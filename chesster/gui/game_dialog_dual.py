from PyQt5 import QtGui, QtSvg, QtWidgets, QtCore
import PyQt5
from PyQt5.QtWidgets import QDialog, QLabel, QMessageBox, QGroupBox, QProgressBar, QRadioButton
from PyQt5.QtGui import QColor, QFont, QImage, QPainter, QPainterPath, QPixmap
from PyQt5.QtSvg import QSvgWidget, QGraphicsSvgItem
from PyQt5.QtChart import QChart, QChartView, QBarSet, QPercentBarSeries, QBarCategoryAxis
from cv2 import QT_RADIOBOX
from sklearn.ensemble import VotingClassifier
#from chesster import Schach_KI
#from chesster.Schach_KI.main import VBC_command
from chesster.gui.utils import get_ui_resource_path
from PyQt5.uic import loadUi
from chesster.Schach_KI.class_chess_gameplay import ChessGameplay
from chesster.master.hypervisor import Hypervisor
from chesster.gui.promotion_dialog import PromotionDialog
import logging
import threading as th
import numpy as np
from PyQt5 import QtMultimedia
from PyQt5.QtCore import QUrl, QSettings
from pathlib import Path

logger = logging.getLogger(__name__)


class GameDialog(QDialog):
    def __init__(self, chess_engine_difficulty, player_color, FlagHints, NoHints, FlagMidgame=False, parent=None):
        super(GameDialog, self).__init__(parent)
        self.parent = parent
        logger.info('Starting Game')
        ui_path = get_ui_resource_path('midgame_and_game_dialog.ui')
        loadUi(ui_path, self)
        #self.promotion_dialog = PromotionDialog(player_color=player_color, parent=self.parent)
        self.NoHints = NoHints
        self.FlagHints = FlagHints
        self.FlagMidgame = FlagMidgame
        self.player_turn = 'w'
        self.__counter=0
        self.round = 0
        self.Checkmate=False
        self.check_fail_flag = False
        self.game_state="NoCheckmate"
        self.remis_state="NoRemis"
        self.Remis = False
        self.HintMove=''
        self.__player_color = player_color
        logger.info('Setting player colors')
        if self.__player_color == 'w':
            logger.info('Human: White | Robot: Black')
            self.__robot_color = 'b'
        else:
            logger.info('Human: Black | Robot: White')
            self.__robot_color = 'w'
        self.BarChart, self.ChartView, self.BarSeries, self.setHuman, self.setAI = self.create_BarChart()
        self.message_box = QMessageBox(self)
        self.message_box.windowTitleChanged.connect(self.show_notify)
        self.message_box_ending = QMessageBox(self)
        self.message_box_ending.windowTitleChanged.connect(self.show_notify_endgame)
        self.message_box_promotion = QMessageBox(self)
        self.message_box_promotion.windowTitleChanged.connect(self.show_notify_promotion)
        self.QueenB = self.message_box_promotion.addButton('Queen', QMessageBox.NoRole)
        self.KnightB = self.message_box_promotion.addButton('Knight', QMessageBox.NoRole)
        self.MidGameButtons = [self.Button_P,
                               self.Button_R, 
                               self.Button_B,
                               self.Button_N,
                               self.Button_Q,
                               self.Button_K,
                               self.Button_p,
                               self.Button_r, 
                               self.Button_b,
                               self.Button_n,
                               self.Button_q,
                               self.Button_k,
                               self.Button_empty]

        self.svg_widget = QSvgWidget()
        self.svg_widget.sizeHint()
        self.svg_widget.setMinimumSize(512, 512)
        self.svg_widget.adjustSize()
        self.gridLayout.addWidget(self.svg_widget)
        self.audioSource = QUrl.fromLocalFile(
            (Path(__file__).parent.absolute() / '../resources/audio/notification_sound.mp3').__str__())
        self.audio = QtMultimedia.QMediaContent(self.audioSource)
        self.audioPlayer = QtMultimedia.QMediaPlayer(parent)
        self.audioPlayer.setMedia(self.audio)
        self.audioPlayer.setVolume(100)
        self.settings = QSettings('chesster', 'options')
        logger.info('Initializing hypervisor')
        self.hypervisor = Hypervisor(self.__robot_color, self.__player_color, chess_engine_difficulty, self.set_notify_promotion)
        logger.info('Hypervisior initialized')
        logger.info('Starting hypervisor')
        self.hypervisor.start()
        logger.info('Hypervisor started')
        image = self.hypervisor.chess_engine.get_drawing('', True, self.__player_color)
        #self.ChessAI = ChessGameplay(skill_level=chess_engine_difficulty)
        logger.info(f'Game Dialog Box started with difficulty: {chess_engine_difficulty} and player color: {player_color}')

        if self.FlagMidgame == True:
            self.enable_midgame_buttons(False)
            self.MidgameButton.clicked.connect(self.chessboard_occupation)
            self.hide_hint_buttons(True)
            self.GameStatus_Text_Label.setText("Please place the chesspieces on the board. Press 'Start' to start defining the positions for the system and wait for further instructions.")
            self.GameButton.setText('Start')
            self.GameButton.setHidden(True)
            self.MidgameButton.setText('Start')
            self.Hint_Label_No.setText(f'{self.NoHints}')
            self.Hint_Label_Hint.setText('')
            self.HintButton.clicked.connect(self.Show_Hint)
            self.hypervisor.set_chessboard_to_empty()
            image = self.hypervisor.chess_engine.get_drawing('', True, self.__player_color, midgame = True)
            #image = self.ChessAI.get_drawing('', True, self.__player_color, midgame = True)
            self.update_drawing(image)
        else:
            self.hide_hint_buttons(True)
            self.hide_midgame_buttons(True)
            image = self.hypervisor.chess_engine.get_drawing('', True, self.__player_color)
            self.update_drawing(image)
            self.GameButton.clicked.connect(self.turn_completed_T)
            self.GameStatus_Text_Label.setText("Please place the chesspieces according to the Image. Press 'Start' to begin the game and wait for further instructions.")
            self.GameButton.setText('Start')
            if FlagHints is True:
                self.hide_hint_buttons(False)
                self.Hint_Label_No.setText(f'{self.NoHints}')
                self.Hint_Label_Hint.setText('')
                self.HintButton.clicked.connect(self.Show_Hint)
            

    def turn_completed(self) -> None:
        """
        main procedure for the game. Only triggers when the human counterfeit finished its move and it's the robots turn
        """
        self.round += 1
        self.GameButton.setText('Move done')
        self.GameButton.setEnabled(False)
        logger.info('Evaluating Game..')
        val_w, val_b = self.hypervisor.chess_engine.chart_data_evaluation()
        #val_w, val_b = self.ChessAI.chart_data_evaluation()
        if self.__player_color == 'w':
            logger.info('Updating Chart for White player color')
            self.update_chart_data([val_w, val_b], self.setHuman, self.setAI)
        else:
            logger.info('Updating Chart for black player color')
            self.update_chart_data([val_b, val_w], self.setHuman, self.setAI)
        #bestmove = self.ChessAI.engine.get_best_move()
        #self.ChessAI.engine.make_moves_from_current_position([bestmove])
        #image=self.ChessAI.get_drawing(bestmove, True, self.__player_color)
        #self.update_drawing(image)


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
                val_w, val_b = self.hypervisor.chess_engine.chart_data_evaluation()
                # val_w, val_b = self.ChessAI.chart_data_evaluation()
                if self.__player_color == 'w':
                    self.update_chart_data([val_w, val_b], self.setHuman, self.setAI)
                else:
                    self.update_chart_data([val_b, val_w], self.setHuman, self.setAI)
        elif self.__counter==0: #Start of game
            logger.info('taking initial images')
            self.hypervisor.update_images()
            if (self.FlagMidgame is False and self.__robot_color == 'w') or (self.FlagMidgame is True and self.__robot_color == self.player_turn): #Robot begins
                self.GameStatus_Text_Label.setText("Robot's move. Wait until the move ended and this instruction changes.")
                self.hypervisor.robot.StartGesture(Beginner=True)
                actions, self.game_state, image, proof, failure_flag, self.remis_state = self.hypervisor.analyze_game(start=True)
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
                    val_w, val_b = self.hypervisor.chess_engine.chart_data_evaluation()
                    # val_w, val_b = self.ChessAI.chart_data_evaluation()
                    if self.__player_color == 'w':
                        self.update_chart_data([val_w, val_b], self.setHuman, self.setAI)
                    else:
                        self.update_chart_data([val_b, val_w], self.setHuman, self.setAI)
                    self.GameStatus_Text_Label.setText("Move done! It's Your turn. Press 'Move done' after you're finished.")
                    self.GameButton.setDisabled(False)
                    if self.game_state != "NoCheckmate": #Check if Robot accomplished Checkmate
                            self.Checkmate = True
                            self.end_game(self.game_state)
                    if self.remis_state != "NoRemis": #Check if Remis occured
                        self.Remis = True
                        self.end_game(self.remis_state)
            else: #Human begins
                self.hypervisor.robot.StartGesture(Beginner=False)
                self.GameStatus_Text_Label.setText("You begin. Press 'Move done' after you're finished.")
                self.GameButton.setDisabled(False)
                self.round-=1
            self.__counter=self.__counter+1

        else: #regular game procedure -> Robot move
            logger.info('Player\'s turn confirmed')
            self.GameStatus_Text_Label.setText("Robot's move. Wait until the move ended and this instruction changes.")
            actions, self.game_state, image, proof, failure_flag, self.remis_state = self.hypervisor.analyze_game(start=False) #First analyze changes and determine proof violation
            if proof == False and self.remis_state == 'NoRemis': #==False = proof violation -> Wrong move detected, if regular move=Robot already rolled back the move
                self.GameButton.setText('Move changed')
                self.GameStatus_Text_Label.setText("Please press 'Move changed' after you have corrected your move.")
                self.GameButton.setDisabled(False)
                self.update_drawing(image) #updated image after human move
                val_w, val_b = self.hypervisor.chess_engine.chart_data_evaluation()
                # val_w, val_b = self.ChessAI.chart_data_evaluation()
                if self.__player_color == 'w':
                    self.update_chart_data([val_w, val_b], self.setHuman, self.setAI)
                else:
                    self.update_chart_data([val_b, val_w], self.setHuman, self.setAI)
                logger.info('opening notify window')
                self.set_notify(f'your recent move {self.hypervisor.last_move_human} was accounted as wrong. Please change your move.', 'Proof Violation')
            elif proof == True and self.remis_state != 'NoRemis':
                self.GameButton.setDisabled(False)
                self.update_drawing(image)  # updated image after human move
                val_w, val_b = self.hypervisor.chess_engine.chart_data_evaluation()
                # val_w, val_b = self.ChessAI.chart_data_evaluation()
                if self.__player_color == 'w':
                    self.update_chart_data([val_w, val_b], self.setHuman, self.setAI)
                else:
                    self.update_chart_data([val_b, val_w], self.setHuman, self.setAI)
                logger.info('opening notify window')
                self.end_game(self.remis_state)
            elif self.remis_state != 'NoRemis':
                self.GameButton.setDisabled(False)
                self.update_drawing(image)  # updated image after human move
                val_w, val_b = self.hypervisor.chess_engine.chart_data_evaluation()
                # val_w, val_b = self.ChessAI.chart_data_evaluation()
                if self.__player_color == 'w':
                    self.update_chart_data([val_w, val_b], self.setHuman, self.setAI)
                else:
                    self.update_chart_data([val_b, val_w], self.setHuman, self.setAI)
                logger.info('opening notify window')
                self.set_notify(
                    f'your recent move {self.hypervisor.last_move_human} was accounted as wrong due to state "Remis"',
                    'Proof Violation')
                self.end_game(self.remis_state)
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
                val_w, val_b = self.hypervisor.chess_engine.chart_data_evaluation()
                # val_w, val_b = self.ChessAI.chart_data_evaluation()
                if self.__player_color == 'w':
                    self.update_chart_data([val_w, val_b], self.setHuman, self.setAI)
                else:
                    self.update_chart_data([val_b, val_w], self.setHuman, self.setAI)
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
                        val_w, val_b = self.hypervisor.chess_engine.chart_data_evaluation()
                        # val_w, val_b = self.ChessAI.chart_data_evaluation()
                        if self.__player_color == 'w':
                            self.update_chart_data([val_w, val_b], self.setHuman, self.setAI)
                        else:
                            self.update_chart_data([val_b, val_w], self.setHuman, self.setAI)
                        self.GameStatus_Text_Label.setText("Move done! It's Your turn again. Press 'Move done' after you're finished.")
                        self.GameButton.setDisabled(False)

                        if self.game_state != "NoCheckmate": #Check if Robot accomplished Checkmate
                            self.Checkmate = True
                            self.end_game(self.game_state)
                        if self.remis_state != "NoRemis": #Check if Remis occured
                            self.Checkmate = True
                            self.end_game(self.remis_state)

    def turn_completed_T(self):
        Thread = th.Thread(target=self.turn_completed)
        Thread.start()

    def Start_FromMidgame(self):
        self.hide_midgame_buttons(True)
        if self.FlagHints is False:
            logger.info('Hints deactivated. Hiding GUI Elements')
            self.hide_hint_buttons(True)
        else:
            logger.info('Hints activated. Show GUI Elements')
            self.hide_hint_buttons(False)
        logger.info('Putting turn_completed_T onto GameButton')
        self.GameButton.clicked.disconnect()
        self.GameButton.clicked.connect(self.turn_completed_T)
        logger.info('Running first iteration of turn_completed.')
        self.turn_completed_T()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        logger.info('Closing')
        #self.hypervisor.stop()
        super(GameDialog, self).close()

    def update_drawing(self, svg_image):
        logger.info('Updating drawing...')
        svg_image = bytes(svg_image, 'utf8')
        self.svg_widget.renderer().load(svg_image)
        self.svg_widget.show()
        audio_state = self.settings.value('audioOn', type=bool, defaultValue=True)
        if audio_state:
            self.audioPlayer.play()
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
        logger.info('Notify window Promotion')
        self.message_box_promotion.setText("You promoted a pawn. Please select the piece you swapped the pawn for.")   

        self.message_box_promotion.setWindowTitle('Promotion!')

    def show_notify_promotion(self):
        logger.info('Notify window Promotion exec')
        self.message_box_promotion.exec()
        if self.message_box_promotion.clickedButton() == self.QueenB:
            if self.__player_color == 'w':
                logger.info('Queen selected')
                self.hypervisor.detector.board.last_promotionfield.state = 'Q'
            else:
                logger.info('Queen selected')
                self.hypervisor.detector.board.last_promotionfield.state = 'q'
        elif self.message_box_promotion.clickedButton() == self.KnightB:
            logger.info('Knight selected')
            if self.__player_color == 'w':
                self.hypervisor.detector.board.last_promotionfield.state = 'N'
            else:
                self.hypervisor.detector.board.last_promotionfield.state = 'n'
        self.message_box_promotion = QMessageBox(self)
        self.message_box_promotion.windowTitleChanged.connect(self.show_notify)
        self.QueenB = self.message_box_promotion.addButton('Queen', QMessageBox.NoRole)
        self.KnightB = self.message_box_promotion.addButton('Knight', QMessageBox.NoRole)

    def end_game(self, state):
        """
        End of the game procedure with Endgestures and space for messages
        """
        if state=="RobotVictory":
            self.set_notify_endgame('You lose! Robot Won! GG. Close this dialog to return to the main menu.', 'Checkmate!')
            self.hypervisor.robot.EndGesture(Victory=True)
        elif state=="HumanVictory":
            self.set_notify_endgame('You Won! Robot lose! GG. Close this dialog to return to the main menu.', 'Checkmate!')
            self.hypervisor.robot.EndGesture(Victory=False)
        elif state == "Movecount":
            self.set_notify_endgame('GG. Game ended up in a Remis by reaching 50 moves without moving a pawn or capturing a piece. Close this dialog to return to the main menu.', 'Remis!')
        elif state == "TripleOccur":
            self.set_notify_endgame('GG. Game ended up in a Remis by triple occurence of the exakt same board. Close this dialog to return to the main menu.', 'Remis!')
        elif state == "Stalemate":
            self.set_notify_endgame('GG. Game ended up in a Remis by stalemate. No move possible, but not Checkmate. Close this dialog to return to the main menu.', 'Remis!')
        else:
            logger.info(f'unknown state for checkmate or remis given')

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
            if self.__player_color == 'w':
                list_HintMove = self.hypervisor.chess_engine.mirrored_play([self.HintMove])
                self.HintMove = list_HintMove[0]
            logger.info('Hint: ' + self.HintMove)
            self.Hint_Label_Hint.setText('Tip from the AI: ' + self.HintMove)
            self.NoHints-=1
            self.Hint_Label_No.setText(f'{self.NoHints}')
            image = self.hypervisor.chess_engine.get_drawing(self.HintMove, True, self.__player_color, hint=True)
            self.update_drawing(image)

    def enable_midgame_buttons(self, Bool: bool) -> None:
        for button in self.MidGameButtons:
            button.setEnabled(Bool)

    def hide_midgame_buttons(self, Bool: bool) -> None:
        for button in self.MidGameButtons:
            button.setHidden(Bool)
        self.MidgameButton.setHidden(Bool)
        self.Input_Field.setHidden(Bool)
        self.groupBox_2.setHidden(Bool)
        self.Field_Label_Text.setHidden(Bool)
        
    def hide_hint_buttons(self, Bool: bool) -> None:
        self.Hint_Label_No.setHidden(Bool)
        self.Hint_Label_Hint.setHidden(Bool)
        self.HintButton.setHidden(Bool)
        self.Hint_Label_Text.setHidden(Bool)

    def chessboard_occupation(self) -> None:
        #self.fields_occ = determine_occupied_fields()
        Pieces = ['P','R','B','N','Q','K','p','r','b','n','q','k']
        self.GameButton.setHidden(False)
        self.enable_midgame_buttons(True)
        self.GameStatus_Text_Label.setText(
            "Please define the states/chesspieces for all used fields. Press 'Start' to begin the game at the actual position and wait for further instructions. If you defined a wrong piece, set it to 'Empty' or place a new piece on that field")
        self.MidgameButton.setHidden(True)
        self.MidgameButton.clicked.disconnect()
        self.GameButton.clicked.connect(self.Start_FromMidgame)
        self.Button_P.clicked.connect(lambda: self.PieceButton_click('P'))
        self.Button_R.clicked.connect(lambda: self.PieceButton_click('R'))
        self.Button_B.clicked.connect(lambda: self.PieceButton_click('B'))
        self.Button_N.clicked.connect(lambda: self.PieceButton_click('N'))
        self.Button_Q.clicked.connect(lambda: self.PieceButton_click('Q'))
        self.Button_K.clicked.connect(lambda: self.PieceButton_click('K'))
        self.Button_p.clicked.connect(lambda: self.PieceButton_click('p'))
        self.Button_r.clicked.connect(lambda: self.PieceButton_click('r'))
        self.Button_b.clicked.connect(lambda: self.PieceButton_click('b'))
        self.Button_n.clicked.connect(lambda: self.PieceButton_click('n'))
        self.Button_q.clicked.connect(lambda: self.PieceButton_click('q'))
        self.Button_k.clicked.connect(lambda: self.PieceButton_click('k'))
        self.Button_empty.clicked.connect(lambda: self.PieceButton_click('.'))

    def PieceButton_click(self, state: str):
        logger.info(f'Writing field {self.Input_Field.text()} with {state}..')
        for radio_button in self.groupBox_2.findChildren(QRadioButton):
            if radio_button.isChecked():
                next_player = radio_button.text().lower()
                logger.info(f'{next_player}')
                if next_player == 'schwarz':
                    next_player = 'black'
                    logger.info(f'{next_player}')
                self.player_turn = next_player[0]
                logger.info(f'{self.player_turn}')
                break
        self.hypervisor.replace_one_field_state(self.Input_Field.text(), state)
        fen = self.hypervisor.compute_fen_from_detector(self.__player_color, self.player_turn)
        logger.info(f'given fen to get_drawing: {fen}')
        #TODO: Button for player_turn as it is necessary for player_turn in FEN
        logger.info(self.hypervisor.detector.get_fields())
        image = self.hypervisor.chess_engine.get_drawing('', True, self.__player_color, midgame=True, fen=fen)
        self.update_drawing(image)

    def create_BarChart(self):
        chart = QChart()
        set0 = QBarSet('Player')
        set1 = QBarSet('AI')
        if self.__player_color =='w':
            set0.setColor(QtGui.QColor("white"))
            set1.setColor(QtGui.QColor("black"))
        else:
            set0.setColor(QtGui.QColor("black"))
            set1.setColor(QtGui.QColor("white"))
        set0 << 50
        set1 << 50
        BarSeries = QPercentBarSeries()
        BarSeries.append(set0)
        BarSeries.append(set1)
        chart.addSeries(BarSeries)
        chart.setTitle('Player vs AI Advantage')
        chart.setAnimationOptions(QChart.SeriesAnimations)
        category = [""]
        axis = QBarCategoryAxis()
        axis.append(category)
        chart.createDefaultAxes()
        chart.setAxisX(axis, BarSeries)
        chart.legend().setVisible(True)
        chartView = QChartView(chart)
        chartView.setRenderHint(QPainter.Antialiasing)
        chart.setBackgroundVisible(False)
        self.ChartLayout.addWidget(chartView)
        return chart, chartView, BarSeries, set0, set1
    
    def update_chart_data(self, update_values: list, series0, series1):
        series0.remove(0)
        series1.remove(0)
        series0.append(update_values[0])
        series1.append(update_values[1])
