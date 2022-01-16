from chesster.camera.realsense import RealSenseCamera
from chesster.master.action import Action
from chesster.obj_recognition.chessboard import ChessBoard
from chesster.Schach_KI.class_chess_gameplay import ChessGameplay
from chesster.Robot.UR10 import UR10Robot
from chesster.vision_based_control.controller import VisualBasedController
import logging
from typing import Callable
from pathlib import Path
import os

logger = logging.getLogger(__name__)


class Hypervisor:
    def __init__(self, logging_func: Callable[[str], None], notification_func):
        logger.info('Hypervisor Construction!')
        self.logger = logging_func
        self.notificator = notification_func
        self.camera = RealSenseCamera(auto_start=False)
        self.robot = UR10Robot(os.environ['ROBOT_ADDRESS'])
        self.chessboard = ChessBoard.load(Path('chessboard.pkl'))
        self.chess_engine = ChessGameplay()
        self.visual_based_controller = VisualBasedController('')
        self.current_board_matrix = None
        self.current_image = None
        self.current_depth_image = None
        self.logger('Hypervisor initialized!')

    def start(self, player_color: str, player_skill_level: int):
        self.logger('Hypervisor starting')
        self.camera.start()
        # TODO: Add support for runtime skill level change in stockfish: stockfish.set_skill_level().
        # See: https://pypi.org/project/stockfish/
        self.chessboard.start_game(player_color, player_skill_level)
        # TODO: Add public start() method to robot
        self.robot.start()

    def stop(self):
        self.camera.stop()
        self.robot.stop()

    def push(self):
        pass

    def update_graphic(self):
        pass
