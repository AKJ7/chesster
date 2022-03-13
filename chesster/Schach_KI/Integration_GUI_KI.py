from PyQt5 import QtGui, QtSvg, QtWidgets, QtCore
import PyQt5
from PyQt5.QtWidgets import QDialog, QLabel, QMessageBox, QGroupBox, QProgressBar, QRadioButton
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QLabel,
                            QGridLayout, QFileDialog)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont, QImage, QPainter, QPainterPath, QPixmap
from PyQt5.QtSvg import QSvgWidget, QGraphicsSvgItem
from PyQt5.QtChart import QChart, QChartView, QBarSet, QPercentBarSeries, QBarCategoryAxis
from cv2 import QT_RADIOBOX
from sklearn.ensemble import VotingClassifier
# from chesster import Schach_KI
# from chesster.Schach_KI.main import VBC_command
from chesster.gui.utils import get_ui_resource_path
from PyQt5.uic import loadUi
from chesster.Schach_KI.class_chess_gameplay import ChessGameplay
from chesster.master.hypervisor import Hypervisor
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
        logger.info('Starting Game')
        ui_path = get_ui_resource_path('midgame_and_game_dialog.ui')
        loadUi(ui_path, self)
        self.NoHints = NoHints
        self.FlagHints = FlagHints
        self.FlagMidgame = FlagMidgame
        self.player_turn = 'w'
        self.__counter = 0
        self.round = 0
        self.Checkmate = False
        self.check_fail_flag = False
        self.game_state = "NoCheckmate"
        self.remis_state = "NoRemis"
        self.Remis = False
        self.HintMove = ''
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
        self.hypervisor = HypervisorKIGUI(self.__robot_color, self.__player_color, chess_engine_difficulty)
        logger.info('Hypervisor initialized')
        #logger.info('Starting hypervisor')
        #self.hypervisor.start()
        #logger.info('Hypervisor started')
        image = self.hypervisor.chess_engine.get_drawing('', True, self.__player_color)
        #self.ChessAI = ChessGameplay(skill_level=chess_engine_difficulty)
        #image = self.ChessAI.get_drawing('', True, self.__player_color)
        logger.info(
            f'Game Dialog Box started with difficulty: {chess_engine_difficulty} and player color: {player_color}')
        self.Input_Field.resize(50, 25)
        if self.FlagMidgame == True:
            self.enable_midgame_buttons(False)
            self.MidgameButton.clicked.connect(self.chessboard_occupation)
            self.hide_hint_buttons(True)
            self.GameStatus_Text_Label.setText(
                "Please place the chesspieces on the board. Press 'Start' to start defining the positions for the system and wait for further instructions.")
            self.GameButton.setText('Start')
            self.GameButton.setHidden(True)
            self.MidgameButton.setText('Start')
            self.Hint_Label_No.setText(f'{self.NoHints}')
            self.Hint_Label_Hint.setText('')
            self.HintButton.clicked.connect(self.Show_Hint)
            #self.hypervisor.set_chessboard_to_empty()
            image = self.hypervisor.chess_engine.get_drawing('', True, self.__player_color, midgame=True)
            #image = self.ChessAI.get_drawing('', True, self.__player_color, midgame = True)
            self.update_drawing(image)
        else:
            self.hide_hint_buttons(True)
            self.hide_midgame_buttons(True)
            image = self.hypervisor.chess_engine.get_drawing('', True, self.__player_color)
            #image = self.ChessAI.get_drawing('', True, self.__player_color)
            self.update_drawing(image)
            self.GameButton.clicked.connect(self.turn_completed_T)
            self.GameStatus_Text_Label.setText(
                "Please place the chesspieces according to the Image. Press 'Start' to begin the game and wait for further instructions.")
            self.GameButton.setText('Start')
            if FlagHints is True:
                self.hide_hint_buttons(False)
                self.Hint_Label_No.setText(f'{self.NoHints}')
                self.Hint_Label_Hint.setText('')
                self.HintButton.clicked.connect(self.Show_Hint)

        #self.end_game("RobotVictory")
        #self.end_game("HumanVictory")
        #self.end_game("Movecount")
        #self.end_game("TripleOccur")
        #self.end_game("Stalemate")


    def turn_completed(self) -> None:
        """
        main procedure for the game. Only triggers when the human counterfeit finished its move and it's the robots turn
        """
        self.round += 1
        self.GameButton.setText('Move done')
        self.GameButton.setEnabled(False)
        self.Input_Field.setHidden(True)
        #val_w, val_b = self.hypervisor.chess_engine.chart_data_evaluation()
        #val_w, val_b = self.ChessAI.chart_data_evaluation()
        #if self.__player_color == 'w':
        #    self.update_chart_data([val_w, val_b], self.setHuman, self.setAI)
        #else:
        #    self.update_chart_data([val_b, val_w], self.setHuman, self.setAI)
        # bestmove = self.ChessAI.engine.get_best_move()
        # self.ChessAI.engine.make_moves_from_current_position([bestmove])
        # image=self.ChessAI.get_drawing(bestmove, True, self.__player_color)
        # self.update_drawing(image)

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
                self.GameStatus_Text_Label.setText(
                    "Detection successful! You may make your move now and press 'Move done' after you're finished.")
                self.GameButton.setDisabled(False)
                self.update_drawing(image)
                val_w, val_b = self.hypervisor.chess_engine.chart_data_evaluation()
                # val_w, val_b = self.ChessAI.chart_data_evaluation()
                if self.__player_color == 'w':
                    self.update_chart_data([val_w, val_b], self.setHuman, self.setAI)
                else:
                    self.update_chart_data([val_b, val_w], self.setHuman, self.setAI)
        elif self.__counter == 0:  # Start of game
            logger.info('taking initial images')
            #self.hypervisor.update_images()
            if self.__robot_color == 'w':  # Robot begins
                self.GameStatus_Text_Label.setText(
                    "Robot's move. Wait until the move ended and this instruction changes.")
                # self.hypervisor.robot.StartGesture(Beginner=True)
                actions, self.game_state, image, proof, failure_flag, self.remis_state = self.hypervisor.analyze_game(
                    start=True, opp_move=self.Input_Field.text())
                self.game_state, image, failure_flag = self.hypervisor.make_move(actions)
                self.update_drawing(image)
                val_w, val_b = self.hypervisor.chess_engine.chart_data_evaluation()
                # val_w, val_b = self.ChessAI.chart_data_evaluation()
                if self.__player_color == 'w':
                    self.update_chart_data([val_w, val_b], self.setHuman, self.setAI)
                else:
                    self.update_chart_data([val_b, val_w], self.setHuman, self.setAI)
                self.GameStatus_Text_Label.setText(
                    "Move done! It's Your turn. Press 'Move done' after you're finished.")
                self.GameButton.setDisabled(False)
                if self.game_state != "NoCheckmate":  # Check if Robot accomplished Checkmate
                    self.Checkmate = True
                    self.end_game(self.game_state)
                if self.remis_state != "NoRemis":  # Check if Remis occured
                    self.Remis = True
                    self.end_game(self.remis_state)
            else:  # Human begins
                # self.hypervisor.robot.StartGesture(Beginner=False)
                self.GameStatus_Text_Label.setText("You begin. Press 'Move done' after you're finished.")
                self.GameButton.setDisabled(False)
                self.round -= 1
            self.__counter = self.__counter + 1

        else:  # regular game procedure -> Robot move
            logger.info('Player\'s turn confirmed')
            self.GameStatus_Text_Label.setText("Robot's move. Wait until the move ended and this instruction changes.")
            move = self.Input_Field.text()
            actions, self.game_state, image, proof, failure_flag, self.remis_state = self.hypervisor.analyze_game(
                start=False, opp_move=self.Input_Field.text())  # First analyze changes and determine proof violation
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
            else:  # Standard case! regular game procedure
                self.update_drawing(image)  # updated image after human move
                val_w, val_b = self.hypervisor.chess_engine.chart_data_evaluation()
                # val_w, val_b = self.ChessAI.chart_data_evaluation()
                if self.__player_color == 'w':
                    self.update_chart_data([val_w, val_b], self.setHuman, self.setAI)
                else:
                    self.update_chart_data([val_b, val_w], self.setHuman, self.setAI)
                if self.game_state != "NoCheckmate":  # Check if Human accomplished Checkmate
                    self.Checkmate = True
                    self.end_game(self.game_state)
                else:  # Moves pieces
                    self.game_state, image, failure_flag = self.hypervisor.make_move(actions)  # make moves received on analyze_game
                    self.update_drawing(image)  # updated image after robot move
                    val_w, val_b = self.hypervisor.chess_engine.chart_data_evaluation()
                    # val_w, val_b = self.ChessAI.chart_data_evaluation()
                    if self.__player_color == 'w':
                        self.update_chart_data([val_w, val_b], self.setHuman, self.setAI)
                    else:
                        self.update_chart_data([val_b, val_w], self.setHuman, self.setAI)
                    self.GameStatus_Text_Label.setText(
                        "Move done! It's Your turn again. Press 'Move done' after you're finished.")
                    self.GameButton.setDisabled(False)

                    if self.game_state != "NoCheckmate":  # Check if Robot accomplished Checkmate
                        self.Checkmate = True
                        self.end_game(self.game_state)
                    if self.remis_state != "NoRemis":  # Check if Remis occured
                        self.Remis = True
                        self.end_game(self.remis_state)
        self.Input_Field.setHidden(False)

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
        super(GameDialog, self).close()

    def update_drawing(self, svg_image):
        logger.info('Updating drawing...')
        svg_image = bytes(svg_image, 'utf8')
        logger.info('Updating drawing1...')
        self.svg_widget.renderer().load(svg_image)
        logger.info('Updating drawing2...')
        self.svg_widget.show()
        logger.info('Updating drawing3...')
        audio_state = self.settings.value('audioOn', type=bool, defaultValue=True)
        logger.info('Updating drawing4...')
        if audio_state:
            logger.info('Updating drawing5...')
            self.audioPlayer.play()
        logger.info('Updating drawing completed.')

    def set_notify(self, message, title='message', icon=QMessageBox.Warning):
        # self.message_box.setIcon(icon)
        self.message_box.setText(message)
        self.message_box.setWindowTitle(title)

    def show_notify(self):
        self.message_box.exec()
        self.message_box = QMessageBox(self)
        self.message_box.windowTitleChanged.connect(self.show_notify)

    def set_notify_endgame(self, message, title='message'):
        self.message_box_ending.setText(message)
        # self.message_box_ending.setIcon(QMessageBox.Information)
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
                self.hypervisor.board_temp.board.last_promotionfield.state = 'Q'
            else:
                self.hypervisor.board_temp.board.last_promotionfield.state = 'q'
        elif self.message_box_promotion.clickedButton() == self.KnightB:
            if self.__player_color == 'w':
                self.hypervisor.board_temp.board.last_promotionfield.state = 'K'
            else:
                self.hypervisor.board_temp.board.last_promotionfield.state = 'k'
        self.message_box_promotion = QMessageBox(self)
        self.message_box_promotion.windowTitleChanged.connect(self.show_notify)

    def end_game(self, state):
        """
        End of the game procedure with Endgestures and space for messages
        """
        if state == "RobotVictory":
            self.set_notify_endgame('You lose! Robot Won! GG. Close this dialog to return to the main menu.',
                                    'Checkmate!')
            #self.hypervisor.robot.EndGesture(Victory=True)
        elif state == "HumanVictory":
            self.set_notify_endgame('You Won! Robot lose! GG. Close this dialog to return to the main menu.',
                                    'Checkmate!')
            #self.hypervisor.robot.EndGesture(Victory=False)
        elif state == "Movecount":
            self.set_notify_endgame(
                'GG. Game ended up in a Remis by reaching 50 moves without moving a pawn or capturing a piece. Close this dialog to return to the main menu.',
                'Remis!')
        elif state == "TripleOccur":
            self.set_notify_endgame(
                'GG. Game ended up in a Remis by triple occurence of the exakt same board. Close this dialog to return to the main menu.',
                'Remis!')
        elif state == "Stalemate":
            self.set_notify_endgame(
                'GG. Game ended up in a Remis by stalemate. No move possible, but not Checkmate. Close this dialog to return to the main menu.',
                'Remis!')
        else:
            logger.info(f'unknown state for checkmate or remis given')

    def Check_Promote(self):
        if self.hypervisor.detector.board.promoting == True:
            logger.info('Promotion detected. Displaying window to get which promotion occured.')

    def Show_Hint(self):
        logger.info('Showing Hint')
        if self.round == 0:
            self.Hint_Label_Hint.setText(
                "It's your turn to start. Please make your first move before you can use hints.")
        elif self.NoHints == 0:
            self.Hint_Label_Hint.setText(
                "Sorry, you used all your available hints! It's only (wo)man versus machine now!")
        else:
            logger.info('Getting Hint from AI')
            self.HintMove = self.hypervisor.chess_engine.engine.get_best_move()
            if self.__player_color == 'w':
                list_HintMove = self.hypervisor.chess_engine.mirrored_play([self.HintMove])
                self.HintMove = list_HintMove[0]
            logger.info('Hint: ' + self.HintMove)
            self.Hint_Label_Hint.setText('Tip from the AI: ' + self.HintMove)
            self.NoHints -= 1
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
        self.groupBox_2.setHidden(Bool)
        #self.Input_Field.setHidden(Bool)
        self.Field_Label_Text.setHidden(Bool)

    def hide_hint_buttons(self, Bool: bool) -> None:
        self.Hint_Label_No.setHidden(Bool)
        self.Hint_Label_Hint.setHidden(Bool)
        self.HintButton.setHidden(Bool)
        self.Hint_Label_Text.setHidden(Bool)

    def chessboard_occupation(self) -> None:
        # self.fields_occ = determine_occupied_fields()
        Pieces = ['P', 'R', 'B', 'N', 'Q', 'K', 'p', 'r', 'b', 'n', 'q', 'k']
        self.GameButton.setHidden(False)
        self.enable_midgame_buttons(True)
        self.GameStatus_Text_Label.setText(
            "Please define the states/chesspieces for all used fields. Press 'Start' to begin the game at the actual position and wait for further instructions. If you defined a wrong piece, set it to 'Empty' or place a new piece on that field")
        self.MidgameButton.setHidden(True)
        self.MidgameButton.clicked.disconnect()
        for radio_button in self.groupBox_2.findChildren(QRadioButton):
            if radio_button.isChecked():
                next_player = radio_button.text().lower()
                self.player_turn = next_player[0]
                break
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
        # TODO: Button for player_turn as it is necessary for player_turn in FEN
        #logger.info(self.hypervisor.detector.get_fields())
        image = self.hypervisor.chess_engine.get_drawing('', True, self.__player_color, midgame=True, fen=fen)
        self.update_drawing(image)

    def create_BarChart(self):
        chart = QChart()
        set0 = QBarSet('Player')
        set1 = QBarSet('AI')
        if self.__player_color == 'w':
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


import faulthandler
from chesster.camera.realsense import RealSenseCamera
from chesster.master.action import Action
from chesster.obj_recognition.chessboard import ChessBoard
from chesster.Schach_KI.class_chess_gameplay import ChessGameplay
from chesster.Robot.UR10 import UR10Robot
from chesster.obj_recognition.object_recognition import ObjectRecognition
from chesster.vision_based_control.controller import VisualBasedController
import logging
from pathlib import Path
import os
import copy
import cv2 as cv
import time
import threading as th

logger = logging.getLogger(__name__)


class HypervisorKIGUI:
    def __init__(self, robot_color, human_color, player_skill_level):
        logger.info('Constructing Hypervisor!')
        #self.camera = RealSenseCamera(auto_start=False)
        #self.robot = UR10Robot(os.environ['ROBOT_ADDRESS'])
        logger.info('UR10 constructed')
        #self.detector = ObjectRecognition(os.environ['CALIBRATION_DATA_PATH'])
        self.chess_engine = ChessGameplay(skill_level=player_skill_level, threads=4, minimum_thinking_time=30,
                                          debug=False)
        logger.info('Chess AI constructed')
        #self.vision_based_controller = VisualBasedController(self.robot, os.environ['NEURAL_NETWORK_PATH'],
                                                             #os.environ['SCALER_PATH'])
        logger.info('Vision based controller constructed')
        logger.info('Hypervisor constructed!')
        #self.__debug_images_path = os.environ['DEBUG_IMAGES_PATH']
        self.__robot_color = robot_color
        self.__human_color = human_color
        self.__ScalingWidth = None
        self.__ScalingHeight = None
        self.__current_chessBoard = None
        self.__previous_chessBoard = None
        self.__current_cimg = None
        self.__current_dimg = None
        self.__previous_cimg = None
        self.__previous_dimg = None
        self.Checkmate = False
        self.Checkmate_player = False
        self.Remis = False
        self.RemisMoves = False
        self.RemisTriple = False
        self.RemisStale = False
        self.Remis_state = "NoRemis"
        self.last_move_human = None
        self.last_move_robot = None
        self.num_move_robot = 0
        self.debug_image = None
        self.board_list = []
        pieces = ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r']
        for row in '12345678':
            for n, column in enumerate('abcdefgh'):
                position = str(column + row)
                if self.__robot_color == 'w':
                    if int(row) == 1:
                        state = pieces[n].upper()
                    elif int(row) == 2:
                        state = 'P'
                    elif int(row) == 7:
                        state = 'p'
                    elif int(row) == 8:
                        state = pieces[n]
                    else:
                        state = '.'
                else:
                    if int(row) == 1:
                        state = pieces[n]
                    elif int(row) == 2:
                        state = 'p'
                    elif int(row) == 7:
                        state = 'P'
                    elif int(row) == 8:
                        state = pieces[n].upper
                    else:
                        state = '.'
                state = '.'
                field = ChessBoardFieldGUI(position, state)
                self.board_list.append(field)
        self.board_temp = ChessBoardGUI(self.board_list)

    def analyze_game(self, start, opp_move):
        logger.info('Analyzing game')
        self.last_move_human = [opp_move]
        if start:
            logger.info('Robot starts the game.')
            actions, self.Checkmate, self.Checkmate_player, self.RemisMoves, self.RemisTriple, self.RemisStale = self.chess_engine.play_ki(
                self.__current_chessBoard, self.__human_color, self.board_temp)
            self.last_move_robot = actions
            if self.RemisMoves is True:
                self.Remis = True
                self.Remis_state = "Movecount"
            elif self.RemisTriple is True:
                self.Remis = True
                self.Remis_state = "TripleOccur"
            elif self.RemisStale is True:
                self.Remis = True
                self.Remis_state = "Stalemate"
            if actions == []:
                image = self.chess_engine.get_drawing('', True, self.__human_color)
            else:
                image = self.chess_engine.get_drawing(self.last_move_robot[0], True, self.__human_color)
            Proof = True
            failure_flag = False
        else:
            logger.info('Starting analyze_game...')
            # self.last_move_human, _ = self.chess_engine.piece_notation_comparison(self.__previous_chessBoard, self.__current_chessBoard, self.__human_color)
            logger.info(f'detected move from human: {self.last_move_human}')
            logger.info('Simulating human move for stockfish...')
            rollback_move, Proof, self.Checkmate_player, self.Checkmate, self.RemisMoves, self.RemisTriple, self.RemisStale = self.chess_engine.play_opponent(
                self.last_move_human, self.__human_color)
            if self.RemisMoves is True:
                self.Remis = True
                self.Remis_state = "Movecount"
            elif self.RemisTriple is True:
                self.Remis = True
                self.Remis_state = "TripleOccur"
            elif self.RemisStale is True:
                self.Remis = True
                self.Remis_state = "Stalemate"
            logger.info('Checking whether the last human move is valid...')
            if Proof is False:
                logger.info(f'Move "{self.last_move_human}" from human invalid...')
                for move in self.last_move_human:
                    if not ('xx' in move) and not (
                            'P' in move):  # only enters statement if the last move is a regular move (eg. e2e4)
                        logger.info('Last move was a regular move. Proceeding to rollback with robot...')
                    else:
                        logger.info('invalid move contains Promotion or Capture. No rollback from robot possible. ')
                logger.info('Returning to GUI.')
                return [], "NoCheckmate", self.chess_engine.get_drawing(self.last_move_human[0], Proof,
                                                                        self.__human_color), Proof, False, self.Remis_state

            logger.info('Checking whether checkmate occured...')
            if self.Checkmate is True:
                logger.info('Checkmate! Human won. leaving analyze_game and starting winning scene...')
                return [], "HumanVictory", self.chess_engine.get_drawing(self.last_move_human[0], Proof,
                                                                         self.__human_color), Proof, False, self.Remis_state
            if self.Checkmate_player is True:
                logger.info('Checkmate! Robot won. leaving analyze_game and starting winning scene...')
                return [], "RobotVictory", self.chess_engine.get_drawing(self.last_move_human[0], Proof,
                                                                         self.__human_color), Proof, False, self.Remis_state
            logger.info('No Checkmate.')
            logger.info('Checking whether remis occured...')
            if self.Remis is True:
                logger.info('Remis! No winner! leaving analyze_game...')
                return [], "No Checkmate", self.chess_engine.get_drawing(self.last_move_human[0], Proof,
                                                                         self.__human_color), Proof, False, self.Remis_state
            logger.info('No Checkmate and no Remis.')

            logger.info('updating chessboard')
            #self.__previous_chessBoard = self.__current_chessBoard
            image = self.chess_engine.get_drawing(self.last_move_human[0], Proof, self.__human_color)
            logger.info('Getting KI move')
            actions, self.Checkmate, self.Checkmate_player, self.RemisMoves, self.RemisTriple, self.RemisStale = self.chess_engine.play_ki(
                self.__previous_chessBoard, self.__human_color, self.board_temp)
            self.last_move_robot = actions
            if self.RemisMoves is True:
                self.Remis = True
                self.Remis_state = "Movecount"
            elif self.RemisTriple is True:
                self.Remis = True
                self.Remis_state = "TripleOccur"
            elif self.RemisStale is True:
                self.Remis = True
                self.Remis_state = "Stalemate"
            if self.Remis is True:
                logger.info('Remis! No winner! leaving analyze_game...')
            logger.info('No Checkmate and no Remis.')
            logger.info(f'actions to be performed from KI: {actions}')
            # Important: Even though self.checkmate may be True (therefor robot won) "NoCheckmate" is still returned. Checkmate will be acknowledged in make_move()
        return actions, "NoCheckmate", image, Proof, False, self.Remis_state

    def make_move(self, actions, debug=False):
        logger.info(f'Performing moves from KI')
        #time.sleep(5)
        self.last_move_robot = actions
        if actions != []:
            logger.info('Checking whether checkmate occured...')
            if self.Checkmate == True:  # Check for checkmate from analyze_game()
                logger.info('Checkmate! Human won. leaving analyze_game and starting winning scene...')
                # self.progress.setValue(100)
                return "HumanVictory", self.chess_engine.get_drawing(self.last_move_robot[0], True,
                                                                     self.__human_color), False  # proof for robot always true
            if self.Checkmate_player == True:  # Check for checkmate from analyze_game()
                logger.info('Checkmate! Robot won. leaving analyze_game and starting winning scene...')
                # self.progress.setValue(100)
                return "RobotVictory", self.chess_engine.get_drawing(self.last_move_robot[0], True,
                                                                     self.__human_color), False  # proof for robot always true
            logger.info('No Checkmate')
            if self.Remis == True:  # Check for remis from analyze_game()
                logger.info('Remis! Nobody won. leaving analyze_game...')
                # self.progress.setValue(100)
                return "NoCheckmate", self.chess_engine.get_drawing(self.last_move_robot[0], True,
                                                                    self.__human_color), False  # proof for robot always true
            logger.info('No Checkmate and no Remis')
            # self.progress.setValue(100)
            logger.info(f'{self.last_move_robot[0]}, {self.__human_color}')
            return "NoCheckmate", self.chess_engine.get_drawing(self.last_move_robot[0], True, self.__human_color), False
        else:
            return "NoCheckmate", self.chess_engine.get_drawing("", True, self.__human_color), False

    def recover_failure(self):
        logger.info(f'New Detection successful.')
        logger.info(f'Detected move by the robot: {self.last_move_robot}')
        image = self.chess_engine.get_drawing(self.last_move_robot[0], True, self.__human_color)

        return False, image

    def set_chessboard_to_empty(self):
        logger.info('setting Fen Position from AI to empty ("")')
        # todo: Set Fen to zero for empty image
        ## Best Thing to do with used engine since a game without two kings is illegal
        self.chess_engine.engine.set_fen_position('4k3/8/8/8/8/8/8/4K3 w - - 0 1')

    def replace_one_field_state(self, field_str: str, new_state: str):
        logger.info(f'Replacing field {field_str} with state {new_state}')
        for field in self.board_temp.fields:
            if field.position == field_str:
                logger.info('field found. replacing.')
                field.state = new_state

    def compute_fen_from_detector(self, player_color, player_turn='w'):
        logger.info(f' started computing FEN')
        fen = ''
        King_w = False
        LTower_w = False
        RTower_w = False
        King_b = False
        LTower_b = False
        RTower_b = False
        w_King_Flag = False
        b_King_Flag = False
        for row in '87654321':
            for column in 'abcdefgh':
                for field in self.board_temp.fields:
                    if field.position == str(column + row):
                        fen += field.state
                    if field.state == 'K':
                        w_King_Flag = True
                    if field.state == 'k':
                        b_King_Flag = True
                    if player_color == 'w':
                        if field.position == 'e1' and field.state == 'K':
                            King_w = True
                        if field.position == 'a1' and field.state == 'R':
                            LTower_w = True
                        if field.position == 'h1' and field.state == 'R':
                            RTower_w = True
                        if field.position == 'e8' and field.state == 'k':
                            King_b = True
                        if field.position == 'a8' and field.state == 'r':
                            LTower_b = True
                        if field.position == 'h8' and field.state == 'r':
                            RTower_b = True
                    else:
                        if field.position == 'e1' and field.state == 'k':
                            King_b = True
                        if field.position == 'a1' and field.state == 'r':
                            LTower_b = True
                        if field.position == 'h1' and field.state == 'r':
                            RTower_b = True
                        if field.position == 'e8' and field.state == 'K':
                            King_w = True
                        if field.position == 'a8' and field.state == 'R':
                            LTower_w = True
                        if field.position == 'h8' and field.state == 'R':
                            RTower_w = True
            if row != '1':
                fen += '/'
        logger.info(f' temporary fen is {fen}')
        fen = fen.replace("........", str(8))
        fen = fen.replace(".......", str(7))
        fen = fen.replace("......", str(6))
        fen = fen.replace(".....", str(5))
        fen = fen.replace("....", str(4))
        fen = fen.replace("...", str(3))
        fen = fen.replace("..", str(2))
        fen = fen.replace(".", str(1))
        rochade = ''
        if King_w is True and RTower_w is True:
            rochade += 'K'
        if King_w is True and LTower_w is True:
            rochade += 'Q'
        if King_b is True and RTower_b is True:
            rochade += 'k'
        if King_b is True and LTower_b is True:
            rochade += 'q'
        if rochade == '':
            rochade = '-'
        fen += ' ' + player_turn + ' ' + rochade + ' - 0 1'

        if w_King_Flag is True and b_King_Flag is True:
            if player_color == 'b':
                self.chess_engine.engine.set_fen_position(fen)
                logger.info(f'Setting FEN-Position in Stockfish succeeded')
            else:
                self.chess_engine.engine.set_fen_position(self.chess_engine.mirror_fen(midgame=True, fen=fen))
                logger.info(f'Setting FEN-Position in Stockfish succeeded')
        else:
            logger.info(f'Not yet a legal FEN-Position because at least one King is missing')
        return fen

class ChessBoardFieldGUI:
    def __init__(self, position: str, state: str):
        self.position = position
        self.state = state
from typing import List, Tuple
class ChessBoardGUI:
    def __init__(self, fields: List[ChessBoardFieldGUI]):
        self.fields = fields
    def return_field(self, chess_field: str):
        for field in self.fields:
            if field.position == chess_field:
                return field
        return None
