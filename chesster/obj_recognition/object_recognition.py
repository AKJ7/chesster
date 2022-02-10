from pathlib import Path
import logging
import os
from typing import Union, Optional
import numpy as np
from chesster.master.module import Module
from chesster.obj_recognition.chessboard_recognition import *
from chesster.obj_recognition.chessboard import *
from chesster.obj_recognition.chesspiece import ChessPiece

logger = logging.getLogger(__name__)


class ObjectRecognition(Module):
    def __init__(self, board_info_path: Union[str, os.PathLike], debug=False):
        logger.info('Initializing Object recognition module!')
        cwd = os.getcwd()
        self.board_info_path = cwd+'\\'+board_info_path
        self.board = ChessBoard.load(self.board_info_path)
        self.debug = debug
        logger.info('Chessboard recognition module initialized!')

    def stop(self):
        logger.info('Stopping Object recognition module!')
        logger.info('Object recognition module stopped!')

    def start(self, com_color='w'):
        self.board.start(com_color)
        logger.info('Starting Object recognition module!')
        logger.info('Chessboard recognition module started!')

    def determine_changes(self, previous: np.ndarray, current_image: np.ndarray, current_player_color:str):
        width, height = self.board.image.shape[:2]
        move = self.board.determine_changes(previous, current_image, width, height, current_player_color, self.debug)
        return self.get_chessboard_matrix(), move

    def get_chesspiece_info(self, chessfield: str, depth_map) -> Optional[ChessPiece]:
        for field in self.board.fields:
            if field.position == chessfield:
                width, height = self.board.image.shape[:2]
                zenith, x, y = field.get_zenith(depth_map, width, height)
                chesspiece = ChessPiece(field.position, field.contour, zenith, x, y)
                return chesspiece
        return None

    def get_chessboard_matrix(self):
        return self.board.current_chess_matrix

    def get_fields(self):
        return self.board.fields
        
    def return_field(self, chessfield: str):
        for field in self.board.fields:
            if field.position == chessfield:
                return field
        return None

    def get_board_visual(self):
        self.board.print_state()

    @staticmethod
    def create_chessboard_data(image: np.ndarray, depth: np.ndarray, output_path: Path, debug=False):
        board = ChessboardRecognition.from_image(image, depth_map=depth, debug=debug)
        board.save(output_path)
        return board
