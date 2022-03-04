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


class Hypervisor:
    def __init__(self, robot_color, human_color, player_skill_level):
        logger.info('Constructing Hypervisor!')
        self.camera = RealSenseCamera(auto_start=False)
        self.robot = UR10Robot(os.environ['ROBOT_ADDRESS'])
        logger.info('UR10 constructed')
        self.detector = ObjectRecognition(os.environ['CALIBRATION_DATA_PATH'])
        self.chess_engine = ChessGameplay(skill_level=player_skill_level, threads=4, minimum_thinking_time=30, debug=False)
        logger.info('Chess AI constructed')
        self.vision_based_controller = VisualBasedController(self.robot, os.environ['NEURAL_NETWORK_PATH'], os.environ['SCALER_PATH'])
        logger.info('Vision based controller constructed')
        logger.info('Hypervisor constructed!')
        self.__debug_images_path = os.environ['DEBUG_IMAGES_PATH']
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

    def start(self):
        logger.info('Hypervisor starting')
        self.camera.start()
        self.robot.start()
        logger.info('UR10 started')
        self.detector.start()
        logger.info('Chess AI started')
        self.vision_based_controller.start()
        logger.info('Vision based controller started')

        self.__ScalingWidth = self.detector.board.scaling_factor_width
        self.__ScalingHeight = self.detector.board.scaling_factor_height
        self.__current_chessBoard = self.detector.get_chessboard_matrix()
        self.__current_cimg = []
        self.__current_dimg = []

    def stop(self):
        self.camera.stop()
        self.robot.stop()
            
    def analyze_game(self, start):
        logger.info('Analyzing game')
        #self.progress.setValue(10)
        if start:
            logger.info('Robot starts the game.')
            #self.progress.setValue(20)
            actions, self.Checkmate, self.Checkmate_player, self.RemisMoves, self.RemisTriple, self.RemisStale = self.chess_engine.play_ki(self.__current_chessBoard, self.__human_color, self.detector)
            if self.RemisMoves is True:
                self.Remis = True
                self.Remis_state = "Movecount"
            elif self.RemisTriple is True:
                self.Remis = True
                self.Remis_state = "TripleOccur"
            elif self.RemisStale is True:
                self.Remis = True
                self.Remis_state = "Stalemate"
            Proof = True
            image = None
            failure_flag = False
            #self.progress.setValue(50)
        else:
            logger.info('Starting analyze_game...')
            logger.info('Making the image from last move to the previous image.')
            self.__previous_cimg = self.__current_cimg.copy()

            logger.info('Taking new images')
            self.__current_cimg = self.camera.capture_color()
            self.__current_dimg, _ = self.camera.capture_depth(apply_filter=True)

            #self.progress.setValue(20)
            logger.info('Overriding chessboard from last move')
            self.__previous_chessBoard = self.__current_chessBoard

            logger.info('Determine changes caused by human move...')
            self.__current_chessBoard, self.last_move_human, failure_flag = self.detector.determine_changes(self.__previous_cimg, self.__current_cimg, self.__human_color)
            logger.info(f'Current Chess board layout after determine changes: {self.detector.get_fields()}')
            #self.progress.setValue(40)
            if failure_flag:
                logger.info('Rolling out detection failure callback')
                logger.info('Rolling back current taken color image, chessboard matrix and board class')
                self.__current_cimg = self.__previous_cimg.copy()
                self.__current_chessBoard = self.__previous_chessBoard
                self.detector.board = copy.deepcopy(self.detector.board_backup)
                return [], "NoCheckmate", None, True, failure_flag, self.Remis_state

            #self.last_move_human, _ = self.chess_engine.piece_notation_comparison(self.__previous_chessBoard, self.__current_chessBoard, self.__human_color)
            logger.info(f'detected move from human: {self.last_move_human}')
            logger.info('Simulating human move for stockfish...')
            rollback_move, Proof, self.Checkmate_player, self.Checkmate, self.RemisMoves, self.RemisTriple, self.RemisStale = self.chess_engine.play_opponent(self.last_move_human, self.__human_color)
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
            #self.progress.setValue(50)
            if Proof is False:
                logger.info(f'Move "{self.last_move_human}" from human invalid...')
                logger.info('Rolling back last cimg and chessboard list...')
                self.__current_cimg = self.__previous_cimg.copy()
                self.__current_chessBoard = self.__previous_chessBoard
                ProofMove = ''
                for move in self.last_move_human:
                    if not('xx' in move) and not('P' in move): #only enters statement if the last move is a regular move (eg. e2e4)
                        logger.info('Last move was a regular move. Proceeding to rollback with robot...')
                        Chesspieces = [self.detector.get_chesspiece_info(rollback_move[0][0:2], self.__current_dimg), self.detector.return_field(rollback_move[0][2:4])]
                        self.vision_based_controller.useVBC(rollback_move, Chesspieces, self.__current_dimg, [self.__ScalingHeight, self.__ScalingWidth], lastMove=True)
                    else:
                        logger.info('invalid move contains Promotion or Capture. No rollback from robot possible. ')
                #self.progress.setValue(90)
                logger.info('Rolling back chessboard class from detector...')
                self.detector.board = copy.deepcopy(self.detector.board_backup) #TBD, necessary to get on old state before irregular move!
                logger.info('Returning to GUI.')
                #self.progress.setValue(100)
                return [], "NoCheckmate", self.chess_engine.get_drawing(self.last_move_human[0], Proof, self.__human_color), Proof, failure_flag, self.Remis_state

            logger.info('Checking whether checkmate occured...')
            if self.Checkmate is True:
                logger.info('Checkmate! Human won. leaving analyze_game and starting winning scene...')
                return [], "HumanVictory", self.chess_engine.get_drawing(self.last_move_human[0], Proof, self.__human_color), Proof, failure_flag, self.Remis_state
            if self.Checkmate_player is True:
                logger.info('Checkmate! Robot won. leaving analyze_game and starting winning scene...')
                return [], "RobotVictory", self.chess_engine.get_drawing(self.last_move_human[0], Proof, self.__human_color), Proof, failure_flag, self.Remis_state
            logger.info('No Checkmate.')
            logger.info('Checking whether remis occured...')
            if self.Remis is True:
                logger.info('Remis! No winner! leaving analyze_game...')
                return [], "No Checkmate", self.chess_engine.get_drawing(self.last_move_human[0], Proof, self.__human_color), Proof, failure_flag, self.Remis_state
            logger.info('No Checkmate and no Remis.')

            logger.info('updating chessboard')
            self.__previous_chessBoard = self.__current_chessBoard
            image = self.chess_engine.get_drawing(self.last_move_human[0], Proof, self.__human_color)
            logger.info('Getting KI move')
            actions, self.Checkmate, self.Checkmate_player, self.RemisMoves, self.RemisTriple, self.RemisStale = self.chess_engine.play_ki(self.__previous_chessBoard, self.__human_color, self.detector)
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
            #self.progress.setValue(100)
            #Important: Even though self.checkmate may be True (therefor robot won) "NoCheckmate" is still returned. Checkmate will be acknowledged in make_move()
        return actions, "NoCheckmate", image, Proof, failure_flag, self.Remis_state

    def make_move(self, actions, debug=False):
        logger.info(f'Performing moves from KI')
        if actions != []:
            for i, move in enumerate(actions):
                logger.info(f'Performing move {i+1}: {move}')
                if 'x' in move:
                    Chesspieces = [self.detector.get_chesspiece_info(move[0:2], self.__current_dimg), None]
                elif 'P' in move:
                    Chesspieces = [None, self.detector.return_field(move[2:])]
                else:
                    Chesspieces = [self.detector.get_chesspiece_info(move[0:2], self.__current_dimg), self.detector.return_field(move[2:])]

                if i == len(actions)-1:
                    logger.info('Last action of move detected. Homing afterwards.')
                    last_move = True
                else:
                    last_move = False
                if debug==True:
                    processed_debug_img = self.process_debug_image(self.debug_image)
                self.vision_based_controller.useVBC(move, Chesspieces, self.__current_dimg, [self.__ScalingHeight, self.__ScalingWidth], last_move)

            logger.info('Overriding images from previous step')
            self.__previous_cimg = self.__current_cimg.copy()
            self.__previous_dimg = self.__current_dimg.copy()
            logger.info('Taking new images')
            self.__current_cimg = self.camera.capture_color()
            self.__current_dimg, _ = self.camera.capture_depth(apply_filter=True)
            self.debug_image = self.__current_cimg.copy()
            #self.progress.setValue(20)
            logger.info('Determining changes produced by the robot')
            self.__current_chessBoard, self.last_move_robot, failure_flag = self.detector.determine_changes(self.__previous_cimg, self.__current_cimg, self.__robot_color)
            logger.info(f'Current Chess board layout after determine changes: {self.detector.get_fields()}')
            #self.progress.setValue(50)
            if failure_flag:
                logger.info('Rolling out detection failure callback')
                logger.info('Rolling back current taken color image, chessboard matrix and board class')
                self.__current_cimg = self.__previous_cimg.copy()
                self.__current_chessBoard = self.__previous_chessBoard
                self.detector.board = copy.deepcopy(self.detector.board_backup)
                #self.progress.setValue(100)
                return "NoCheckmate", None, failure_flag

            logger.info(f'Detected move by the robot: {self.last_move_robot}')
            self.num_move_robot = self.num_move_robot + 1
            logger.info('Checking whether checkmate occured...')
            if self.Checkmate == True: #Check for checkmate from analyze_game()
                logger.info('Checkmate! Human won. leaving analyze_game and starting winning scene...')
                #self.progress.setValue(100)
                return "HumanVictory", self.chess_engine.get_drawing(self.last_move_robot[0], True, self.__human_color), failure_flag #proof for robot always true
            if self.Checkmate_player == True: #Check for checkmate from analyze_game()
                logger.info('Checkmate! Robot won. leaving analyze_game and starting winning scene...')
                #self.progress.setValue(100)
                return "RobotVictory", self.chess_engine.get_drawing(self.last_move_robot[0], True, self.__human_color), failure_flag #proof for robot always true
            logger.info('No Checkmate')
            if self.Remis == True: #Check for remis from analyze_game()
                logger.info('Remis! Nobody won. leaving analyze_game...')
                #self.progress.setValue(100)
                return "NoCheckmate", self.chess_engine.get_drawing(self.last_move_robot[0], True, self.__human_color), failure_flag #proof for robot always true
            logger.info('No Checkmate and no Remis')
            #self.progress.setValue(100)
            return "NoCheckmate", self.chess_engine.get_drawing(self.last_move_robot[0], True, self.__human_color), failure_flag
        else:
            return "NoCheckmate", self.chess_engine.get_drawing("", True, self.__human_color), False

    def recover_failure(self):
        logger.info('Recovering from failure.')
        logger.info('Overriding images from previous step')
        self.__previous_cimg = self.__current_cimg.copy()
        self.__previous_dimg = self.__current_dimg.copy()
        logger.info('Taking new images')
        self.__current_cimg = self.camera.capture_color()
        self.__current_dimg, _ = self.camera.capture_depth(apply_filter=True)
        self.__current_chessBoard, self.last_move_robot, failure_flag = self.detector.determine_changes(self.__previous_cimg, self.__current_cimg, self.__robot_color)
        if failure_flag:
            logger.info('Detection failed again.')
            logger.info('Rolling back current taken color image, chessboard matrix and board class')
            self.__current_cimg = self.__previous_cimg.copy()
            self.__current_chessBoard = self.__previous_chessBoard
            self.detector.board = copy.deepcopy(self.detector.board_backup)
            return failure_flag, None
        logger.info(f'New Detection successful.')
        logger.info(f'Detected move by the robot: {self.last_move_robot}')
        image = self.chess_engine.get_drawing(self.last_move_robot[0], True, self.__human_color)

        return failure_flag, image

    def set_chessboard_to_empty(self):
        logger.info('setting from detector chessboard all states to empty (.)')
        for field in self.detector.board.fields:
            field.state = '.'
        logger.info('setting Fen Position from AI to empty ("")')
        #todo: Set Fen to zero for empty image
        ## Best Thing to do with used engine since a game without two kings is illegal
        self.chess_engine.engine.set_fen_position('4k3/8/8/8/8/8/8/4K3 w - - 0 1')
    
    def replace_one_field_state(self, field_str: str, new_state: str):
        logger.info(f'Replacing field {field_str} with state {new_state}')
        for field in self.detector.board.fields:
            if field.position == field_str:
                logger.info('field found. replacing.')
                field.state = new_state
    
    def update_images(self):
        self.__current_cimg = self.camera.capture_color()
        self.__current_dimg, _ = self.camera.capture_depth(apply_filter=True)
        logger.info(self.__current_dimg.shape)
        self.debug_image = self.__current_cimg.copy()

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
                for field in self.detector.board.fields:
                    if field.position == str(column+row):
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

    def process_debug_image(self, debug_image) -> None:
        new_coords = []
        if self.detector.dumped_coords != None:
            for i in range(len(self.detector.dumped_coords[0])):
                new_coords.append([self.detector.dumped_coords[0][i], self.detector.dumped_coords[1][i]])
            for coords in new_coords:
                x = coords[0]
                y = coords[1]
                cv.circle(debug_image, (y,x), 2, (0,0,255), -1)
            cv.circle(debug_image, (self.detector.debug_y, self.detector.debug_x), 2, (255,0,0), -1)
            self.ShowImagesT(debug_image)

    def ShowImagesT(self, Image):
        Thread = th.Thread(target=self.ShowImages, args=(Image,))
        Thread.start()

    def ShowImages(self, debug_image):
        file_time = time.strftime("%d_%m_%Y_%H_%M_%S")
        cv.destroyAllWindows()
        cv.imwrite(self.__debug_images_path+f'debug_image_zeniths_{file_time}.png', debug_image)
        cv.imshow('Zeniths found for current chesspiece', debug_image)
        cv.waitKey(0)
