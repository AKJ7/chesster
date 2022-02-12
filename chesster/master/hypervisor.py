from chesster.camera.realsense import RealSenseCamera
from chesster.master.action import Action
from chesster.obj_recognition.chessboard import ChessBoard
from chesster.Schach_KI.class_chess_gameplay import ChessGameplay
from chesster.Robot.UR10 import UR10Robot
from chesster.obj_recognition.object_recognition import ObjectRecognition
from chesster.vision_based_control.controller import VisualBasedController
import logging
from typing import Callable
from pathlib import Path
import os

logger = logging.getLogger(__name__)


class Hypervisor:
    def __init__(self, logging_func: Callable[[str], None], notification_func, robot_color, human_color, player_skill_level):
        logger.info('Hypervisor Construction!')
        self.logger = logger
        self.notificator = notification_func
        self.camera = RealSenseCamera(auto_start=False)
        self.logger.info('RealSenseCamera constructed')
        self.robot = UR10Robot(os.environ['ROBOT_ADDRESS'])
        self.logger.info('UR10 constructed')
        self.detector = ObjectRecognition(os.environ['CALIBRATION_DATA_PATH'])
        self.logger.info('Object Recognition constructed')
        self.chess_engine = ChessGameplay(skill_level=player_skill_level, threads=4, minimum_thinking_time=30, debug=False)
        self.logger.info('Chess AI constructed')
        self.vision_based_controller = VisualBasedController(self.robot, os.environ['NEURAL_NETWORK_PATH'], os.environ['SCALER_PATH'])
        self.logger.info('Vision based controller constructed')
        self.logger.info('Hypervisor constructed!')

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
        self.last_move_human = None
        self.last_move_robot = None
        self.num_move_robot = 0

    def start(self):
        self.logger.info('Hypervisor starting')
        self.camera.start()
        self.logger.info('RealSenseCamera started')
        self.robot.start()
        self.logger.info('UR10 started')
        self.detector.start()
        self.logger.info('Object Recognition started')
        self.logger.info('Chess AI started')
        self.vision_based_controller.start()
        self.logger.info('Vision based controller started')

        self.__ScalingWidth = self.detector.board.scaling_factor_width
        self.__ScalingHeight = self.detector.board.scaling_factor_height
        self.__current_chessBoard = self.detector.get_chessboard_matrix()
        self.__current_cimg = self.camera.capture_color()
        self.__current_dimg, _ = self.camera.capture_depth()

    def stop(self):
        self.camera.stop()
        self.robot.stop()

    def push(self):
        pass

    def update_graphic(self):
        pass

    def make_move(self, start:bool) -> bool:
        if start:
            actions, _, self.Checkmate, _ = self.chess_engine.play_ki(self.__current_chessBoard, self.__human_color, self.detector)
        else:
            self.__previous_cimg = self.__current_cimg.copy()

            self.__current_cimg = self.camera.capture_color()
            self.__current_dimg, _ = self.camera.capture_depth()

            self.__previous_chessBoard = self.__current_chessBoard

            self.logger.info('First Determine Changes...')
            self.__current_chessBoard, self.last_move_human = self.detector.determine_changes(self.__previous_cimg, self.__current_cimg, self.__human_color)
            #self.last_move_human, _ = self.chess_engine.piece_notation_comparison(self.__previous_chessBoard, self.__current_chessBoard, self.__human_color)

            _, Proof, _, self.Checkmate = self.chess_engine.play_opponent([self.last_move_human], self.__human_color)

            if self.Checkmate == True:
                return "HumanVictory", self.chess_engine.get_drawing(), Proof

            if Proof == False:
                print('PROOF FALSE')
                self.__current_cimg = self.__previous_cimg.copy()
                return "NoCheckmate", self.chess_engine.get_drawing(), Proof

            self.__previous_chessBoard = self.__current_chessBoard

            actions, _, self.Checkmate, _ = self.chess_engine.play_ki(self.__previous_chessBoard, self.__human_color, self.detector)
        
        for i, move in enumerate(actions):
            if 'x' in move:
                Chesspieces = [self.detector.get_chesspiece_info(move[0:2], self.__current_dimg), None]
            elif 'P' in move:
                Chesspieces = [None, self.detector.return_field(move[2:])]
            else:
                Chesspieces = [self.detector.get_chesspiece_info(move[0:2], self.__current_dimg), self.detector.return_field(move[2:])]
            
            if i == len(actions)-1:
                print('Last move of given action -> Homing after move')
                last_move = True
            else:
                last_move = False

            self.vision_based_controller.useVBC(move, Chesspieces, self.__current_dimg, [self.__ScalingHeight, self.__ScalingWidth], last_move)

        self.__previous_cimg = self.__current_cimg.copy()
        self.__previous_dimg = self.__current_dimg.copy()

        self.__current_cimg = self.camera.capture_color()
        self.__current_dimg, _ = self.camera.capture_depth()

        self.logger.info('Second Determine Changes...')
        self.__current_chessBoard, self.last_move_robot = self.detector.determine_changes(self.__previous_cimg, self.__current_cimg, self.__robot_color)

        self.num_move_robot = self.num_move_robot + 1

        if self.Checkmate == True:
            return "RobotVictory", self.chess_engine.get_drawing(), Proof

        return "NoCheckmate", self.chess_engine.get_drawing(), Proof

            
