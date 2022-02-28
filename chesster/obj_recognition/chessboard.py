from __future__ import annotations

__all__ = [
    'ChessBoard',
    'ChessBoardField'
]

import cv2 as cv
import numpy as np
from typing import List, Tuple
import pickle
from pathlib import Path
from queue import PriorityQueue
import logging
import time
from chesster.obj_recognition.chessboard_field import ChessBoardField
from chesster.master.game_state import PieceColor
from matplotlib import pyplot as plt
from io import StringIO

logger = logging.getLogger(__name__)


class ChessBoard:
    CHANGE_THRESHOLD = 43

    def __init__(self, fields: List[ChessBoardField], image, depth_map, chessboard_edges, scaling_factor_width,
                 scaling_factor_height) -> None:
        self.fields = fields
        self.board_matrix = []
        self.capture = False
        self.promoting = False
        self.state_change: List[ChessBoardField] = []
        self.last_promotionfield = None
        self.promotion = 'q'
        self.promo = False
        self.move = []
        self.image = image
        self.depth_map = depth_map
        self.chessboard_edge = chessboard_edges
        self.scaling_factor_width = scaling_factor_width
        self.scaling_factor_height = scaling_factor_height
        self.color = 'w'

    @property
    def edges(self):
        return self.chessboard_edge

    def total_detected_fields(self):
        return len(self.fields)

    def draw_fields(self, image):
        for field in self.fields:
            field.draw(image, (255, 0, 0), thickness=2)
            field.draw_roi(image, (0, 255, 0), thickness=2)
            field.classify(image)

    def draw_empty_colors(self, image):
        for field in self.fields:
            field.draw(image)

    def save(self, path: Path):
        with open(path, 'wb') as dest:
            pickle.dump(self, dest)
            logger.info(f'Successfully saved chess data to "{path}"')

    @property
    def corners(self):
        return [[x.c1, x.c2, x.c3, x.c4] for x in self.fields]

    def get_corners(self):
        return [[x.c1, x.c2, x.c3, x.c4] for x in self.fields]

    @staticmethod
    def load(path: Path) -> ChessBoard:
        with open(path, 'rb') as src:
            board = pickle.load(src)
            logger.info(f'Successfully loaded chess data from {path}')
        return board

    def start(self, com_color='w'):
        pieces = ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r']
        if com_color != 'w':
            for x in range(8):
                for y in range(4):
                    temp = self.fields[x + 8*y].position
                    self.fields[x + 8*y].position = self.fields[7-x + 8*(7-y)].position
                    self.fields[7-x + 8*(7-y)].position = temp
            for i in range(8):
                self.fields[i + 7*8].state = pieces[i]
                self.fields[i + 6*8].state = 'p'
                self.fields[i + 5*8].state = '.'
                self.fields[i + 4*8].state = '.'
                self.fields[i + 3*8].state = '.'
                self.fields[i + 2*8].state = '.'
                self.fields[i + 1*8].state = 'P'
                self.fields[i + 0*8].state = pieces[i].upper()
        else:
            for i in range(8):
                self.fields[i + 0*8].state = pieces[i]
                self.fields[i + 1*8].state = 'p'
                self.fields[i + 2*8].state = '.'
                self.fields[i + 3*8].state = '.'
                self.fields[i + 4*8].state = '.'
                self.fields[i + 5*8].state = '.'
                self.fields[i + 6*8].state = 'P'
                self.fields[i + 7*8].state = pieces[i].upper()
        self.color = com_color
        self.board_matrix.append([x.state for x in self.fields])

    def determine_changes(self, previous, current, current_player_color: str, debug=True):
        self.capture = False
        self.promoting = False
        self.state_change, distances, largest_field, second_largest_field = \
            self.__extract_changes(self.fields, previous, current)
        return self.__extract_move(previous, current, self.state_change, distances, largest_field, second_largest_field,
                                   current_player_color)

    @staticmethod
    def __extract_changes(fields: List[ChessBoardField], previous_image, current_image) -> \
            Tuple[List[ChessBoardField], List[float], ChessBoardField, ChessBoardField]:
        distances = []
        state_changes = []
        largest_dist = 0
        second_largest_dist = 0
        largest_field = None
        second_largest_field = None
        for field in fields:
            color_previous = field.roi_color(previous_image)
            color_current = field.roi_color(current_image)
            total = 0
            for i in range(3):
                total += (color_current[i] - color_previous[i]) ** 2
            distance = np.sqrt(total)
            if distance > ChessBoard.CHANGE_THRESHOLD:
                distances.append(distance)
                state_changes.append(field)
            if distance > largest_dist:
                second_largest_field = largest_field
                second_largest_dist = largest_dist
                largest_dist = distance
                largest_field = field
            elif distance > second_largest_dist:
                second_largest_dist = distance
                second_largest_field = field
        logger.info(f'Total changes found: {len(state_changes)}, States: {list(zip(state_changes, distances))}')
        return state_changes, distances, largest_field, second_largest_field

    def __extract_move(self, previous, current, state_change, distances, largest_field, second_largest_field,
                       current_player_color: str):
        failure_flag = False
        total_changes = len(state_change)
        if total_changes == 3:
            count = 0
            count_needed_rows_for_enp = 0
            for state in self.state_change:
                if count == 0:
                    field_1 = self.state_change[count]
                    count = count + 1
                if count == 1:
                    field_2 = self.state_change[count]
                    count = count + 1
                if count == 2:
                    field_3 = self.state_change[count]
            if field_1.row == 4 or field_1.row == 5:
                count_needed_rows_for_enp = count_needed_rows_for_enp + 1
            if field_2.row == 4 or field_2.row == 5:
                count_needed_rows_for_enp = count_needed_rows_for_enp + 1
            if field_3.row == 4 or field_3.row == 5:
                count_needed_rows_for_enp = count_needed_rows_for_enp + 1
            if count_needed_rows_for_enp == 2:
                if field_1.row == field_2.row and field_1.row == field_3.row:
                    self.move = [field_3.position + field_2.position, field_1.position + 'xx']
                    field_1.state = '.'
                    field_2.state = field_3.state
                    field_3.state = '.'
                elif field_1.row == field_3.row and field_1.row == field_2.row:
                    self.move = [field_2.position + field_3.position, field_1.position + 'xx']
                    field_1.state = '.'
                    field_3.state = field_2.state
                    field_2.state = '.'
                elif field_2.row == field_1.row and field_2.row == field_3.row:
                    self.move = [field_3.position + field_1.position, field_2.position + 'xx']
                    field_2.state = '.'
                    field_1.state = field_3.state
                    field_3.state = '.'
                elif field_2.row == field_3.row and field_2.row == field_1.row:
                    self.move = [field_1.position + field_3.position, field_2.position + 'xx']
                    field_2.state = '.'
                    field_3.state = field_1.state
                    field_1.state = '.'
                elif field_3.row == field_1.row and field_3.row == field_2.row:
                    self.move = [field_2.position + field_1.position, field_3.position + 'xx']
                    field_3.state = '.'
                    field_1.state = field_2.state
                    field_2.state = '.'
                elif field_3.row == field_2.row and field_3.row == field_1.row:
                    self.move = [field_1.position + field_2.position, field_3.position + 'xx']
                    field_3.state = '.'
                    field_2.state = field_1.state
                    field_1.state = '.'
                else:
                    self.state_change.pop(min(range(len(distances)), key=distances.__getitem__))
                    logger.error(f'No relative valid En-Passant recognized!')
                    logger.error(f'Current state changes: {list(zip(state_change, distances))}')
                    ChessBoard.__dump_current_input(previous, current)
            else:
                self.state_change.pop(min(range(len(distances)), key=distances.__getitem__)) #pop smallest element
                logger.info(f'no relative valid en-passant was recognized')
                logger.error(f'Current state changes: {list(zip(state_change, distances))}')
                ChessBoard.__dump_current_input(previous, current)
        if total_changes == 4:
            rochade_flag = False
            king_movement_from_1 = False
            king_movement_short_to_1 = False
            king_movement_long_to_1 = False
            king_movement_from_8 = False
            king_movement_short_to_8 = False
            king_movement_long_to_8 = False
            rook_movement_long_from_1 = False
            rook_movement_short_from_1 = False
            rook_movement_long_from_8 = False
            rook_movement_short_from_8 = False
            rook_movement_long_to_1 = False
            rook_movement_short_to_1 = False
            rook_movement_long_to_8 = False
            rook_movement_short_to_8 = False
            used_fields = []
            for state in self.state_change:
                if state.position == 'e1':
                    king_movement_from_1 = True
                elif state.position == 'g1':
                    king_movement_short_to_1 = True
                elif state.position == 'c1':
                    king_movement_long_to_1 = True
                elif state.position == 'e8':
                    king_movement_from_8 = True
                elif state.position == 'g8':
                    king_movement_short_to_8 = True
                elif state.position == 'c8':
                    king_movement_long_to_8 = True
                elif state.position == 'a1':
                    rook_movement_long_from_1 = True
                elif state.position == 'h1':
                    rook_movement_short_from_1 = True
                elif state.position == 'a8':
                    rook_movement_long_from_8 = True
                elif state.position == 'h8':
                    rook_movement_short_from_8 = True
                elif state.position == 'd1':
                    rook_movement_long_to_1 = True
                elif state.position == 'f1':
                    rook_movement_short_to_1 = True
                elif state.position == 'd8':
                    rook_movement_long_to_8 = True
                elif state.position == 'f8':
                    rook_movement_short_to_8 = True
            if king_movement_from_1 and king_movement_short_to_1 and rook_movement_short_from_1 and rook_movement_short_to_1:
                self.move = ['e1g1', 'h1f1']
                rochade_flag = True
            elif king_movement_from_8 and king_movement_short_to_8 and rook_movement_short_from_8 and rook_movement_short_to_8:
                self.move = ['e8g8', 'h8f8']
                rochade_flag = True
            elif king_movement_from_1 and king_movement_long_to_1 and rook_movement_long_from_1 and rook_movement_long_to_1:
                self.move = ['e1c1', 'a1d1']
                rochade_flag = True
            elif king_movement_from_8 and king_movement_long_to_8 and rook_movement_long_from_8 and rook_movement_long_to_8:
                self.move = ['e8c8', 'a8d8']
                rochade_flag = True
            else:
                logger.info(f'no valid Rochade recognized')
                logger.info('Assuming two state_changes were wrong')
                logger.info(f'Seen changes: {self.state_change}')
                logger.info(f'Corresponding distances: {distances}')
                logger.info('Taking the two greatest distances as state change and deleting the smallest...')
                self.state_change.pop(min(range(len(distances)), key=distances.__getitem__)) #pop smallest element
                logger.info(f'New state_change list: {self.state_change}')
                self.state_change.pop(min(range(len(distances)), key=distances.__getitem__)) #pop smallest element
                logger.info(f'New state_change list: {self.state_change}')
            if rochade_flag is True:
                for i in range(len(self.move)):
                    used_fields.append(self.move[i][0:2])
                    used_fields.append(self.move[i][2:4])
                logger.info(f'used fields are: {used_fields}')
                for n, move in enumerate(used_fields):
                    if (n % 2) == 0:
                        for field in self.state_change:
                            if move == field.position:
                                logger.info(f'ran into modulo 1 for n= {n} and move= {move}')
                                field_from = field
                    elif (n % 2) == 1:
                        for field in self.state_change:
                            if move == field.position:
                                logger.info(f'ran into modulo 1 for n= {n} and move= {move}')
                                field_to = field
                                field_to.state = field_from.state
                                field_from.state = '.'
        if total_changes == 2:
            field_one = largest_field
            field_two = second_largest_field
            one_curr = field_one.roi_color(current)
            two_curr = field_two.roi_color(current)
            sum_curr1 = 0
            sum_curr2 = 0
            for i in range(3):
                sum_curr1 += (one_curr[i] - field_one.empty_color[i]) ** 2
                sum_curr2 += (two_curr[i] - field_two.empty_color[i]) ** 2
            dist_curr1 = np.sqrt(sum_curr1)
            dist_curr2 = np.sqrt(sum_curr2)
            if current_player_color == PieceColor.WHITE:
                if dist_curr1 < dist_curr2:
                    self.move = self.check_piece_capture(field_two, field_one)
                    field_two.state = field_one.state
                    field_one.state = '.'
                    self.move = self.check_piece_promotion(self.move, field_two)
                else:
                    self.move = self.check_piece_capture(field_one, field_two)
                    field_one.state = field_two.state
                    field_two.state = '.'
                    self.move = self.check_piece_promotion(self.move, field_one)
            else:
                if dist_curr1 > dist_curr2:
                    self.move = self.check_piece_capture(field_one, field_two)
                    field_one.state = field_two.state
                    field_two.state = '.'
                    self.move = self.check_piece_promotion(self.move, field_one)
                else:
                    self.move = self.check_piece_capture(field_two, field_one)
                    field_two.state = field_one.state
                    field_one.state = '.'
                    self.move = self.check_piece_promotion(self.move, field_two)
        if 2 > total_changes > 4:
            failure_flag = True
            logger.error(f'Invalid number of state changes: {len(self.state_change)} detected!')
            logger.error(f'Detection: {list(zip(self.state_change, distances))}')
            ChessBoard.__dump_current_input(previous, current)
        logger.info(f'Moves: {self.move}, is_error: {failure_flag}, changes_detected: {total_changes}')
        return self.move, failure_flag, total_changes

    @staticmethod
    def __dump_current_input(previous_image, current_image) -> None:
        file_time = time.strftime("%d_%m_%Y_%H_%M_%S")
        previous_file_name = f'failed_detection_previous_{file_time}.png'
        current_file_name = f'failed_detection_current_{file_time}.png'
        logger.info(f'Writing invalid images to "{previous_file_name}" and "{current_file_name}"')
        cv.imwrite(previous_file_name, previous_image)
        cv.imwrite(current_file_name, current_image)

    def check_piece_capture(self, field_to: ChessBoardField, field_from: ChessBoardField):
        if field_to.state != '.':
            self.capture = True
            move_list = [f'{field_from.position}{field_to.position}', f'{field_to.position}xx']
        else:
            move_list = [f'{field_from.position}{field_to.position}']
        return move_list

    def check_piece_promotion(self, moves: List[str], field_to: ChessBoardField):
        self.promoting = False
        if (field_to.state == 'P' and field_to.row == 8) or (field_to.state == 'p' and field_to.row == 1):
            self.promoting = True
            self.last_promotionfield = field_to
            # TODO: Get user input
            field_to.state = 'Q' if field_to.state.isupper() else 'q'
            if len(moves) == 2:
                moves = [moves[0] + field_to.state, moves[1]]
            else:
                moves = [moves[0] + field_to.state]
        return moves

    @property
    def current_chess_matrix(self):
        matrix = []
        for i in range(8):
            matrix.append([])
            for j in range(8):
                matrix[i].append(self.fields[i * 8 + (7 - j)].state)
        return matrix

    def print_state(self, flipped=False) -> str:
        matrix = self.current_chess_matrix
        dump = StringIO()
        letters = '  a   b   c   d   e   f   g   h  '
        print('\n', file=dump, flush=True)
        for i in range(8):
            print('+---+---+---+---+---+---+---+---+', file=dump)
            for j in range(8):
                print(f'| {matrix[7-i][7-j] if flipped else matrix[i][j]} ', end='', file=dump)
            print(f'| {i+1 if flipped else 8-i}', file=dump)
        print('+---+---+---+---+---+---+---+---+', file=dump)
        print(letters[::-1 if flipped else 1], file=dump)
        return str(dump.getvalue())
