#from types import NoneType
from typing import Union, Optional
from pathlib import Path
import numpy as np
import logging
import os
from chesster.master.module import Module
from chesster.obj_recognition.chessboard_recognition import *
from chesster.obj_recognition.chessboard import *
from chesster.obj_recognition.chesspiece import ChessPiece
import cv2 as cv
from matplotlib import pyplot as plt
import copy 
logger = logging.getLogger(__name__)


class ObjectRecognition(Module):
    def __init__(self, board_info_path: Union[str, os.PathLike], debug=False):
        logger.info('Initializing Object recognition module!')
        self.board_info_path = board_info_path
        self.board = ChessBoard.load(Path(self.board_info_path))
        self.debug = debug
        self.dumped_coords = None
        self.dumped_extracted = None
        self.debug_x = None
        self.debug_y = None
        if self.debug:
            ChessboardRecognition.debug_plot(self.board.image, cv.COLOR_BGR2RGB, 'Empty chessboard image')
            temp = self.board.image.copy()
            self.board.draw_fields(temp)
            ChessboardRecognition.debug_plot(temp, cv.COLOR_BGR2RGB, 'Fields of chessboard image')
            temp2 = self.board.image.copy()
            temp2 = cv.cvtColor(temp2, cv.COLOR_BGR2RGB)
            self.board.draw_empty_colors(temp2)
            ChessboardRecognition.debug_plot(temp2, color_map=None, title=None)
        logger.info('Chessboard recognition module initialized!')

    def stop(self):
        logger.info('Stopping Object recognition module!')

    def start(self, com_color='w'):
        logger.info('Starting Object recognition module!')
        self.board.start(com_color)

    def determine_changes(self, previous: np.ndarray, current_image: np.ndarray, current_player_color: str):
        self.board_backup = copy.deepcopy(self.board)
        move, failure_flag, self.NoStateChanges = self.board.determine_changes(previous, current_image,
                                                                               current_player_color, self.debug)
        return self.get_chessboard_matrix(), move, failure_flag

    def get_chesspiece_info(self, chessfield: str, depth_map) -> Optional[ChessPiece]:
        for field in self.board.fields:
            if field.position == chessfield:
                width, height = self.board.image.shape[:2]
                zenith, x, y, extraced, coords = field.get_zenith(depth_map)
                self.dumped_coords = coords
                self.dumped_extracted = extraced
                self.debug_x = x
                self.debug_y = y
                chesspiece = ChessPiece(field.position, field.contour, zenith, x, y)
                return chesspiece
        return None

    def get_chessboard_matrix(self):
        return self.board.current_chess_matrix

    def get_fields(self):
        return self.board.fields
        
    def return_field(self, chess_field: str):
        for field in self.board.fields:
            if field.position == chess_field:
                return field
        return None

    def get_board_visual(self, flipped=False) -> str:
        return self.board.print_state(flipped)

    @staticmethod
    def create_chessboard_data(image: np.ndarray, depth: np.ndarray, output_path: Path, debug=False):
        board = ChessboardRecognition.from_image(image, depth_map=depth, debug=debug)
        board.save(output_path)
        return board
