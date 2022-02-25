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
import logging
from matplotlib import pyplot as plt

logger = logging.getLogger(__name__)


class ChessBoardField:
    def __init__(self, image, c1: Tuple[float, float], c2, c4, c3, position: str, state=''):
        self.c1 = c1
        self.c2 = c2
        self.c3 = c3
        self.c4 = c4
        self.position = position
        self.contour = np.array([c1, c2, c3, c4], dtype=np.int32)
        center = cv.moments(self.contour)
        cx, cy = int(center['m10'] / center['m00']), int(center['m01'] / center['m00'])
        self.roi = (cx, cy)
        self.radius = 10
        self.empty_color = self.roi_color(image, *image.shape[:2])
        self.state = state
        self.shape = image.shape
        #self.image = image.copy()
        #cv.imshow(f'{self.position}', self.image)

    def draw(self, image, color, original_width, original_height, thickness=1, Scaling = False):
        width, height = image.shape[:2]
        ratio_x, ratio_y = self.get_ratio(width, height, original_width, original_height)
        contours = map(lambda x: (x[0] * ratio_x, x[1] * ratio_y), self.contour)
        ctr = np.array(list(contours)).reshape((-1, 1, 2)).astype(np.int32)

        if Scaling == True:
            M = cv.moments(ctr)
            cx = int(M['m10']/M['m00'])
            cy = int(M['m01']/M['m00'])
            cnt_norm = ctr - [cx, cy]
            cnt_scaled = cnt_norm * 0.4 #Scaling Factor -> 0.5 still works fine
            cnt_scaled = cnt_scaled + [cx, cy]
            ctr = cnt_scaled.astype(np.int32)
        cv.drawContours(image, [ctr], 0, color, thickness)

    def draw_roi(self, image, color, original_width=None, original_height=None, thickness=1):
        width, height = image.shape[:2]
        ratio_x, ratio_y = self.get_ratio(width, height, original_width, original_height)
        rescaled_roi_x = int(self.roi[0] * ratio_x)
        rescaled_roi_y = int(self.roi[1] * ratio_y)
        rescaled_roi = (rescaled_roi_x, rescaled_roi_y)
        # cv.putText(image, self.position, rescaled_roi, fontFace=cv.FONT_HERSHEY_SIMPLEX, fontScale=0.5, color=color, thickness=thickness)
        cv.circle(image, rescaled_roi, self.radius, color, thickness)

    def roi_color(self, image, original_width=None, original_height=None):
        width, height = image.shape[:2]
        ratio_x, ratio_y = self.get_ratio(width, height, original_width, original_height)
        rescaled_roi_x = int(self.roi[0] * ratio_x)
        rescaled_roi_y = int(self.roi[1] * ratio_y)
        rescaled_roi = [rescaled_roi_x, rescaled_roi_y]
        mask_image = np.zeros((image.shape[0], image.shape[1]), np.uint8)
        mask_image = cv.circle(mask_image, rescaled_roi, self.radius, (255, 255, 255), -1)
        #self.draw(mask_image, (255, 255, 255), original_width, original_height, -1)
        #self.draw(image, (255, 255, 255), original_width, original_height, -1)
        #cv.imwrite('CTestimg.png', image)
        #cv.imwrite('MaskTestimg.png', mask_image)
        temp = image.copy()
        temp = cv.cvtColor(image, cv.COLOR_BGR2HSV)
        average_raw = cv.mean(temp, mask=mask_image)[::-1]
        average = (int(average_raw[1]), int(average_raw[2]), int(average_raw[3]))
        #cv.imwrite(f'Field {self.position}_maskimage.png', mask_image)
        #cv.imwrite(f'Field {self.position}_image.png', image)
        average_raw_rgb = cv.mean(image, mask=mask_image)[::-1]
        average_rgb = (int(average_raw_rgb[1]), int(average_raw_rgb[2]), int(average_raw_rgb[3]))
        return average

    def classify(self, image):
        rgb = self.roi_color(image, *image.shape[:2])
        s = 0
        for i in range(0, 3):
            s += (self.empty_color[i] - rgb[i]) ** 2
        cv.putText(image, self.position, self.roi, cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv.LINE_AA)

    def get_zenith(self, depth_map, original_width=None, original_height=None) -> np.ndarray:
        width, height = depth_map.shape
        ratio_x, ratio_y = self.get_ratio(width, height, original_width, original_height)
        contours = map(lambda x: (x[0] * ratio_x, x[1] * ratio_y), self.contour)
        edges = np.expand_dims(list(contours), axis=1).astype(np.int32) #vorher 1
        Scaling = True
        # scaling edges/contours -> This can be helpful to prevent wrong pose estimation due to
        # big chess pieces palced near smaller ones and therefor the zenith estimation
        # takes the wrong piece's height (overlapping -> see Intel Realsenseviewer)
        if Scaling == True:
            M = cv.moments(edges)
            cx = int(M['m10']/M['m00'])
            cy = int(M['m01']/M['m00'])
            cnt_norm = edges - [cx, cy]
            cnt_scaled = cnt_norm * 0.4 # Scaling Factor -> 0.5 still works fine
            cnt_scaled = cnt_scaled + [cx, cy]
            edges = cnt_scaled.astype(np.int32)
        mask = np.zeros(depth_map.shape[:2]).astype(np.uint8)
        cv.fillConvexPoly(mask, edges, 255, 1)
        extracted = np.zeros_like(depth_map)
        extracted[mask == 255] = depth_map[mask == 255]
        coords = np.where(extracted == np.amin(extracted[(mask==255) & (extracted>0)]))
        x = coords[0][0]
        y = coords[1][0]
        return np.amin(extracted[(mask==255) & (extracted>0)]), x, y

    def get_ratio(self, current_width, current_height, width=None, height=None):
        if width is None and height is None:
            return self.shape[0] / current_width, self.shape[1] / current_height
        return current_width / width, current_height / height

    def __repr__(self):
        return str({'state': self.state, 'position': self.position, 'edges': [self.c1, self.c2, self.c3, self.c4]})


class ChessBoard:
    CHANGE_THRESHOLD = 30

    def __init__(self, fields: List[ChessBoardField], image, depth_map, chessboard_edges, scaling_factor_width,
                 scaling_factor_height) -> None:
        self.fields = fields
        self.board_matrix = []
        self.capture = False
        self.promoting = False
        self.state_change = []
        self.last_promotionfield = None
        self.promotion = 'q'
        self.promo = False
        self.move = ''
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

    def draw(self, image):
        width, height = self.image.shape[:2]
        for field in self.fields:
            field.draw(image, (0, 0, 255), width, height)
            field.draw_roi(image, (0, 255, 0), width, height)

    def save(self, path: Path):
        with open(path, 'wb') as dest:
            pickle.dump(self, dest)
            logger.info(f'Successfully saved chess data to {path}')

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
                self.fields[8 * i + 7].state = pieces[i]
                self.fields[8 * i + 6].state = 'p'
                self.fields[8 * i + 5].state = '.'
                self.fields[8 * i + 4].state = '.'
                self.fields[8 * i + 3].state = '.'
                self.fields[8 * i + 2].state = '.'
                self.fields[8 * i + 1].state = 'P'
                self.fields[8 * i + 0].state = pieces[i].upper()
        else:
            for i in range(8):
                self.fields[8*i + 0].state = pieces[i]
                self.fields[8*i + 1].state = 'p'
                self.fields[8*i + 2].state = '.'
                self.fields[8*i + 3].state = '.'
                self.fields[8*i + 4].state = '.'
                self.fields[8*i + 5].state = '.'
                self.fields[8*i + 6].state = 'P'
                self.fields[8*i + 7].state = pieces[i].upper()
        self.color = com_color
        self.board_matrix.append([x.state for x in self.fields])

    def determine_changes(self, previous, current, width, height, current_play_color: str, debug=True):
        copy = current.copy()
        copy_previous = previous.copy()
        debug = False
        largest_field = 0
        second_largest_field = 0
        largest_dist = 0
        second_largest_dist = 0
        self.state_change = []
        distances = []
        failure_flag = False
        self.capture = False
        self.promoting = False
        for sq in self.fields:
            color_previous = sq.roi_color(previous, width, height)
            color_current = sq.roi_color(current, width, height)
            
            total = 0
            for i in range(3):
                total += (color_current[i] - color_previous[i]) ** 2
            distance = np.sqrt(total)
            logger.info(f'Field: {sq.position}, ROI Prev: {color_previous}, ROI Curr: {color_current}, Distance: {distance}')
            if distance > 43: #20: #43:
                distances.append(distance)
                self.state_change.append(sq)
            if distance > largest_dist:
                second_largest_field = largest_field
                second_largest_dist = largest_dist
                largest_dist = distance
                largest_field = sq
            elif distance > second_largest_dist:
                # update second change in color
                second_largest_dist = distance
                second_largest_field = sq
            elif distance > second_largest_dist:
                # update third change in color
                third_largest_dist = distance
                third_largest_field = sq
            elif distance > second_largest_dist:
                # update second change in color
                fourth_largest_dist = distance
                fourth_largest_field = sq

        if len(self.state_change) == 1 or len(self.state_change) == 0 or len(self.state_change) > 4 : #failure backup: only one state_change, zero changes or more than 4 detected.
            failure_flag = True
            logger.info(f' {len(self.state_change)} change(s) detected. Proceeding with failure callback.')
            logger.info(f'Seen state changes: {self.state_change}')
            logger.info(f'Seen corresponding distances: {distances}')
            logger.info('writing images for reference to root')
            cv.imwrite("Failed_Detection_Current.png", current)
            cv.imwrite("Failed_Detection_Previous.png", previous)
            return None, failure_flag, len(self.state_change)

        if len(self.state_change) == 3: #En passant state -> Check BEFORE if len(state_change)==2 because of fallback for three (one falsely) detected changes
            logger.info('CASE: 3 Stage_Changes')
            print(f'Seen state changes: {self.state_change}')
            print(f'Seen corresponding distances: {distances}')
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
            if field_1.position[1:2] == '4' or field_1.position[1:2] == '5':
                count_needed_rows_for_enp = count_needed_rows_for_enp + 1
            if field_2.position[1:2] == '4' or field_2.position[1:2] == '5':
                count_needed_rows_for_enp = count_needed_rows_for_enp + 1
            if field_3.position[1:2] == '4' or field_3.position[1:2] == '5':
                count_needed_rows_for_enp = count_needed_rows_for_enp + 1
            if count_needed_rows_for_enp == 2:
                logger.info('Check for En passant')
                if field_1.position[0:1] == field_2.position[0:1] and field_1.position[1:2] == field_3.position[1:2]:
                    self.move = [field_3.position + field_2.position, field_1.position + 'xx']
                    field_1.state = '.'
                    field_2.state = field_3.state
                    field_3.state = '.'
                elif field_1.position[0:1] == field_3.position[0:1] and field_1.position[1:2] == field_2.position[1:2]:
                    self.move = [field_2.position + field_3.position, field_1.position + 'xx']
                    field_1.state = '.'
                    field_3.state = field_2.state
                    field_2.state = '.'
                elif field_2.position[0:1] == field_1.position[0:1] and field_2.position[1:2] == field_3.position[1:2]:
                    self.move = [field_3.position + field_1.position, field_2.position + 'xx']
                    field_2.state = '.'
                    field_1.state = field_3.state
                    field_3.state = '.'
                elif field_2.position[0:1] == field_3.position[0:1] and field_2.position[1:2] == field_1.position[1:2]:
                    self.move = [field_1.position + field_3.position, field_2.position + 'xx']
                    field_2.state = '.'
                    field_3.state = field_1.state
                    field_1.state = '.'
                elif field_3.position[0:1] == field_1.position[0:1] and field_3.position[1:2] == field_2.position[1:2]:
                    self.move = [field_2.position + field_1.position, field_3.position + 'xx']
                    field_3.state = '.'
                    field_1.state = field_2.state
                    field_2.state = '.'
                elif field_3.position[0:1] == field_2.position[0:1] and field_3.position[1:2] == field_1.position[1:2]:
                    self.move = [field_1.position + field_2.position, field_3.position + 'xx']
                    field_3.state = '.'
                    field_2.state = field_1.state
                    field_1.state = '.'
                else:
                    logger.info(f'no relative valid en-passant was recognized')
                    logger.info('Assuming one state_change was wrong')
                    logger.info(f'Seen changes: {self.state_change}')
                    logger.info(f'Corresponding distances: {distances}')
                    logger.info('Taking the two greatest distances as state change and deleting the smallest...')
                    self.state_change.pop(min(range(len(distances)), key=distances.__getitem__)) #pop smallest element
                    logger.info(f'New state_change list: {self.state_change}')
            else:
                logger.info(f'no relative valid en-passant was recognized')
                logger.info('Assuming one state_change was wrong')
                logger.info(f'Seen changes: {self.state_change}')
                logger.info(f'Corresponding distances: {distances}')
                logger.info('Taking the two greatest distances as state change and deleting the smallest...')
                self.state_change.pop(min(range(len(distances)), key=distances.__getitem__)) #pop smallest element
                logger.info(f'New state_change list: {self.state_change}')

        if len(self.state_change) == 4:  #Rocharde
            logger.info('CASE: 4 Stage_Changes')
            print(f'Seen state changes: {self.state_change}')
            print(f'Seen corresponding distances: {distances}')
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
            if king_movement_from_1 is True and king_movement_short_to_1 is True and rook_movement_short_from_1 is True and rook_movement_short_to_1 is True:
                self.move = ['e1g1', 'h1f1']
                rochade_flag = True
            elif king_movement_from_8 is True and king_movement_short_to_8 is True and rook_movement_short_from_8 is True and rook_movement_short_to_8 is True:
                self.move = ['e8g8', 'h8f8']
                rochade_flag = True
            elif king_movement_from_1 is True and king_movement_long_to_1 is True and rook_movement_long_from_1 is True and rook_movement_long_to_1 is True:
                self.move = ['e1c1', 'a1d1']
                rochade_flag = True
            elif king_movement_from_8 is True and king_movement_long_to_8 is True and rook_movement_long_from_8 is True and rook_movement_long_to_8 is True:
                self.move = ['e8c8', 'a8d8']
                rochade_flag = True
            else:

                logger.info(f'no valid Rochade recognized')
                print(f'Seen changes: {len(self.state_change)}')
                logger.info('Assuming two state_changes were wrong')
                logger.info(f'Seen changes: {self.state_change}')
                logger.info(f'Corresponding distances: {distances}')
                logger.info('Taking the two greatest distances as state change and deleting the smallest...')
                self.state_change.pop(min(range(len(distances)), key=distances.__getitem__)) #pop smallest element
                logger.info(f'New state_change list: {self.state_change}')
                self.state_change.pop(min(range(len(distances)), key=distances.__getitem__)) #pop smallest element
                logger.info(f'New state_change list: {self.state_change}')
                #raise RuntimeError(f'Invalid moves: {self.state_change}')
            if rochade_flag is True:
                for i in range(len(self.move)):
                    used_fields.append(self.move[i][0:2])
                    used_fields.append(self.move[i][2:4])
                logger.info(f'used fields are: {used_fields}')
                for n, move in enumerate(used_fields):
                    if (n % 2) == 0:
                        for field in self.state_change:
                            if move == field.position:
                                logger.info(f'ran into modolo 1 for n= {n} and move= {move}')
                                field_from = field
                    elif (n % 2) == 1:
                        for field in self.state_change:
                            if move == field.position:
                                logger.info(f'ran into modolo 1 for n= {n} and move= {move}')
                                field_to = field
                                field_to.state = field_from.state
                                field_from.state = '.'

        if len(self.state_change) == 2: #normal case: regular move
            logger.info('CASE: 2 Stage_Changes')
            field_one = largest_field
            field_two = second_largest_field
            logger.info(f'Field one: {field_one}; field two: {field_two}')
            if debug:
                field_one.draw(copy, (255, 0, 0), 2)
                field_two.draw(copy, (255, 0, 0), 2)
            one_curr = field_one.roi_color(current, width, height)
            two_curr = field_two.roi_color(current, width, height)
            sum_curr1 = 0
            sum_curr2 = 0
            for i in range(0, 3):
                sum_curr1 += (one_curr[i] - field_one.empty_color[i]) ** 2
                sum_curr2 += (two_curr[i] - field_two.empty_color[i]) ** 2
            dist_curr1 = np.sqrt(sum_curr1)
            dist_curr2 = np.sqrt(sum_curr2)
            logger.info(f'Field one dist: {dist_curr1}; field two dist: {dist_curr2}')
            logger.info(f'Color Value of empty Field one: {field_one.empty_color}, Field two: {field_two.empty_color}')
            if current_play_color == "w":
                if dist_curr1 < dist_curr2:
                    logger.info('Case 1')
                    # capture for possible rollback
                    self.move = self.proof_capture(field_from=field_one, field_to=field_two)
                    field_two.state = field_one.state
                    field_one.state = '.'
                    # promotion
                    self.move = self.proof_promotion(moves=self.move, field_to=field_two)
                    # TODO: window asking for promoting piece
                else:
                    logger.info('Case 2')
                    # capture for possible rollback
                    self.move = self.proof_capture(field_from=field_two, field_to=field_one)
                    field_one.state = field_two.state
                    field_two.state = '.'
                    ## self.move = [field_two.position + field_one.position]
                    # promotion
                    self.move = self.proof_promotion(moves=self.move, field_to=field_one)
                    # TODO: window asking for promoting piece
            else:
                if dist_curr1 > dist_curr2:
                    logger.info('Case 3')
                    # capture for possible rollback
                    self.move = self.proof_capture(field_from=field_two, field_to=field_one)
                    field_one.state = field_two.state
                    field_two.state = '.'
                    ## self.move = [field_two.position + field_one.position]
                    self.move = self.proof_promotion(moves=self.move, field_to=field_one)
                    # TODO: window asking for promoting piece
                else:
                    logger.info('Case 4')
                    # capture for possible rollback
                    self.move = self.proof_capture(field_from=field_one, field_to=field_two)
                    field_two.state = field_one.state
                    field_one.state = '.'
                    ### self.move = [field_one.position + field_two.position]
                    # promotion
                    self.move = self.proof_promotion(moves=self.move, field_to=field_two)
                    # TODO: window asking for promoting piece

            print(f'Seen state changes: {self.state_change}')
            print(f'Seen corresponding distances: {distances}')
        return self.move, failure_flag, len(self.state_change)

    def proof_capture(self, field_to: object, field_from: object):
        if field_to.state != '.':
            self.capture = True
            move_list = [field_from.position + field_to.position, field_to.position + 'xx']
        else:
            move_list = [field_from.position + field_to.position]

        return move_list

    def proof_promotion(self, moves: list, field_to: object):
        # promotion
        if field_to.state == 'P' and (field_to.position[1:2] == 1 or field_to.position[1:2] == 8):
            self.promoting = True
            field_to.state == 'Q'
            self.last_promotionfield = field_to
        elif field_to.state == 'p' and (field_to.position[1:2] == 1 or field_to.position[1:2] == 8):
            self.promoting = True
            field_to.state == 'q'
            self.last_promotionfield = field_to
        if self.promoting is True:
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
                matrix[i].append(self.fields[i + 8 * j].state)
        return matrix

    def print_state(self):
        matrix = self.current_chess_matrix
        for i in range(8):
            print('+---+---+---+---+---+---+---+---+')
            for j in range(8):
                if self.color == 'w':
                    print(f'| {matrix[i][j]} ', end='')
                else:
                    print(f'| {matrix[7-i][7-j]} ', end='')
            print(f'| {8-i}')
        print('+---+---+---+---+---+---+---+---+')
        print('  a   b   c   d   e   f   g   h  ')
