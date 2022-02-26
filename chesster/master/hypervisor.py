import faulthandler
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
import copy

logger = logging.getLogger(__name__)


class Hypervisor:
    def __init__(self, logging_func: Callable[[str], None], robot_color, human_color, player_skill_level):
        logger.info('Hypervisor Construction!')
        self.logger = logger
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
        self.__current_cimg = []
        self.__current_dimg, _ = []

    def stop(self):
        self.camera.stop()
        self.robot.stop()

    def push(self):
        pass

    def update_graphic(self):
        pass
    """
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

            rollback_move, Proof, _, self.Checkmate = self.chess_engine.play_opponent([self.last_move_human], self.__human_color)

            if self.Checkmate == True:
                return "HumanVictory", self.chess_engine.get_drawing(), Proof

            logger.info('Checking whether the last human move is valid...')
            if Proof == False:

                logger.info(f'Move "{self.last_move_human}" from human invalid...')
                self.__current_cimg = self.__previous_cimg.copy()
                if not('xx' in self.last_move_human) and not('P' in self.last_move_human): #only enters statement if the last move is a regular move (eg. e2e4)
                    logger.info('Last move was a regular move. Proceeding to rollback...') 
                    Chesspieces = [self.detector.get_chesspiece_info(rollback_move[0:2], self.__current_dimg), self.detector.return_field(rollback_move[2:])]
                    self.vision_based_controller.useVBC(rollback_move, Chesspieces, self.__current_dimg, [self.__ScalingHeight, self.__ScalingWidth], lastMove=True)
                else:
                    logger.info('invalid move contains Promotion or Capture. No rollback possible. ')
                logger.info('Returning to GUI and rolling back taken images and moves.')
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
        """
            
    def analyze_game(self, start):
        self.logger.info('Analyzing game')
        if start:
            self.logger.info('Robot starts the game.')
            actions, _, self.Checkmate, _ = self.chess_engine.play_ki(self.__current_chessBoard, self.__human_color, self.detector)
            Proof = True
            image = None
            failure_flag = False
        else:
            self.logger.info('Starting analyze_game...')
            self.logger.info('Making the image from last move to the previous image.')
            self.__previous_cimg = self.__current_cimg.copy()

            self.logger.info('Taking new images')
            self.__current_cimg = self.camera.capture_color()
            self.__current_dimg, _ = self.camera.capture_depth()

            self.logger.info('Overriding chessboard from last move')
            self.__previous_chessBoard = self.__current_chessBoard

            self.logger.info('Determine changes caused by human move...')
            self.__current_chessBoard, self.last_move_human, failure_flag = self.detector.determine_changes(self.__previous_cimg, self.__current_cimg, self.__human_color)
            if failure_flag:
                self.logger.info('Rolling out detection failure callback')
                self.logger.info('Rolling back current taken color image, chessboard matrix and board class')
                self.__current_cimg = self.__previous_cimg.copy()
                self.__current_chessBoard = self.__previous_chessBoard
                self.detector.board = copy.deepcopy(self.detector.board_backup)
                return [], "NoCheckmate", None, True, failure_flag

            #self.last_move_human, _ = self.chess_engine.piece_notation_comparison(self.__previous_chessBoard, self.__current_chessBoard, self.__human_color)
            self.logger.info(f'detected move from human: {self.last_move_human}')
            self.logger.info('Simulating human move for stockfish...')
            rollback_move, Proof, _, self.Checkmate = self.chess_engine.play_opponent(self.last_move_human, self.__human_color)

            self.logger.info('Checking whether the last human move is valid...')
            if Proof == False:
                self.logger.info(f'Move "{self.last_move_human}" from human invalid...')
                self.logger.info('Rolling back last cimg and chessboard list...')
                self.__current_cimg = self.__previous_cimg.copy()
                self.__current_chessBoard = self.__previous_chessBoard
                ProofMove = ''
                for move in self.last_move_human:
                    ProofMove=ProofMove+move
                if not('xx' in ProofMove) and not('P' in ProofMove): #only enters statement if the last move is a regular move (eg. e2e4)
                    self.logger.info('Last move was a regular move. Proceeding to rollback with robot...') 
                    Chesspieces = [self.detector.get_chesspiece_info(rollback_move[0][0:2], self.__current_dimg), self.detector.return_field(rollback_move[0][2:4])]
                    self.vision_based_controller.useVBC(rollback_move, Chesspieces, self.__current_dimg, [self.__ScalingHeight, self.__ScalingWidth], lastMove=True)
                else:
                    self.logger.info('invalid move contains Promotion or Capture. No rollback from robot possible. ')
            
                self.logger.info('Rolling back chessboard class from detector...')
                self.detector.board = copy.deepcopy(self.detector.board_backup) #TBD, necessary to get on old state before irregular move!
                self.logger.info('Returning to GUI.')
                return [], "NoCheckmate", self.chess_engine.get_drawing(self.last_move_human[0], Proof, self.__human_color), Proof, failure_flag

            self.logger.info('Checking whether checkmate occured...')
            if self.Checkmate == True:
                self.logger.info('Checkmate! Human won. leaving analyze_game and starting winning scene...')
                return [], "HumanVictory", self.chess_engine.get_drawing(self.last_move_human[0], Proof, self.__human_color), Proof, failure_flag
            self.logger.info('No Checkmate.')
            self.logger.info('updating chessboard')
            self.__previous_chessBoard = self.__current_chessBoard
            image = self.chess_engine.get_drawing(self.last_move_human[0], Proof, self.__human_color)
            self.logger.info('Getting KI move')
            actions, _, self.Checkmate, _ = self.chess_engine.play_ki(self.__previous_chessBoard, self.__human_color, self.detector) 
            self.logger.info(f'actions to be performed from KI: {actions}')
            #Important: Even though self.checkmate may be True (therefor robot won) "NoCheckmate" is still returned. Checkmate will be acknowledged in make_move()
        return actions, "NoCheckmate", image, Proof, failure_flag

    def make_move(self, actions):
        self.logger.info(f'Performing moves from KI')
        for i, move in enumerate(actions):
            self.logger.info(f'Performing move {i+1}: {move}')
            if 'x' in move:
                Chesspieces = [self.detector.get_chesspiece_info(move[0:2], self.__current_dimg), None]
            elif 'P' in move:
                Chesspieces = [None, self.detector.return_field(move[2:])]
            else:
                Chesspieces = [self.detector.get_chesspiece_info(move[0:2], self.__current_dimg), self.detector.return_field(move[2:])]
            
            if i == len(actions)-1:
                self.logger.info('Last action of move detected. Homing afterwards.')
                last_move = True
            else:
                last_move = False

            self.vision_based_controller.useVBC(move, Chesspieces, self.__current_dimg, [self.__ScalingHeight, self.__ScalingWidth], last_move)

        self.logger.info('Overriding images from previous step')
        self.__previous_cimg = self.__current_cimg.copy()
        self.__previous_dimg = self.__current_dimg.copy()
        self.logger.info('Taking new images')                                                                                                                                                                                                                                                                                                                                                                                                                                        
        self.__current_cimg = self.camera.capture_color()
        self.__current_dimg, _ = self.camera.capture_depth()

        self.logger.info('Determining changes produced by the robot')
        self.__current_chessBoard, self.last_move_robot, failure_flag = self.detector.determine_changes(self.__previous_cimg, self.__current_cimg, self.__robot_color)
        if failure_flag:
            self.logger.info('Rolling out detection failure callback')
            self.logger.info('Rolling back current taken color image, chessboard matrix and board class')
            self.__current_cimg = self.__previous_cimg.copy()
            self.__current_chessBoard = self.__previous_chessBoard
            self.detector.board = copy.deepcopy(self.detector.board_backup)
            return "NoCheckmate", None, failure_flag
        
        self.logger.info(f'Detected move by the robot: {self.last_move_robot}')
        self.num_move_robot = self.num_move_robot + 1
        self.logger.info('Checking whether checkmate occured...')
        if self.Checkmate == True: #Check for checkmate from analyze_game()
            self.logger.info('Checkmate! Robot won. leaving analyze_game and starting winning scene...')
            return "RobotVictory", self.chess_engine.get_drawing(self.last_move_robot[0], True, self.__human_color), failure_flag #proof for robot always true
        self.logger.info('No Checkmate')
        return "NoCheckmate", self.chess_engine.get_drawing(self.last_move_robot[0], True, self.__human_color), failure_flag

    def recover_failure(self):
        self.logger.info('Recovering from failure.')
        self.logger.info('Overriding images from previous step')
        self.__previous_cimg = self.__current_cimg.copy()
        self.__previous_dimg = self.__current_dimg.copy()
        self.logger.info('Taking new images')                                                                                                                                                                                                                                                                                                                                                                                                                                        
        self.__current_cimg = self.camera.capture_color()
        self.__current_dimg, _ = self.camera.capture_depth()
        self.__current_chessBoard, self.last_move_robot, failure_flag = self.detector.determine_changes(self.__previous_cimg, self.__current_cimg, self.__robot_color)
        if failure_flag:
            self.logger.info('Detection failed again.')
            self.logger.info('Rolling back current taken color image, chessboard matrix and board class')
            self.__current_cimg = self.__previous_cimg.copy()
            self.__current_chessBoard = self.__previous_chessBoard
            self.detector.board = copy.deepcopy(self.detector.board_backup)
            return failure_flag, None
        self.logger.info(f'New Detection successful.')
        self.logger.info(f'Detected move by the robot: {self.last_move_robot}')
        image = self.chess_engine.get_drawing(self.last_move_robot[0], True, self.__human_color)

        return failure_flag, image

    def set_chessboard_to_empty(self):
        logger.info('setting from detector chessboard all states to empty (.)')
        for field in self.detector.board.fields:
            field.state = '.'
        logger.info('setting Fen Position from AI to empty ("")')
        #todo: Set Fen to zero for empty image
    
    def replace_one_field_state(self, field_str: str, new_state: str):
        logger.info(f'Replacing field {field_str} with state {new_state}')
        for field in self.detector.board.fields:
            if field.position == field_str:
                logger.info('field found. replacing.')
                field.state = new_state
    
    def update_images(self):
        self.__current_cimg = self.camera.capture_color()
        self.__current_dimg, _ = self.camera.capture_depth()