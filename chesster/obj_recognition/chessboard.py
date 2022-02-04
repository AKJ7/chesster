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
        self.empty_color = self.roi_color(image)
        self.state = state

    def draw(self, image, color, thickness=2):
        ctr = np.array(self.contour).reshape((-1, 1, 2)).astype(np.int32)
        cv.drawContours(image, [ctr], 0, color, thickness)

    def draw_roi(self, image, color, thickness=3):
        cv.circle(image, self.roi, self.radius, color, thickness)

    def roi_color(self, image, original_width, original_height):
        width, height = image.shape[:2]
        ratio_x, ratio_y = width / original_width, height / original_height
        rescaled_roi_x = int(self.roi[0] * ratio_x)
        rescaled_roi_y = int(self.roi[1] * ratio_y)
        rescaled_roi = [rescaled_roi_x, rescaled_roi_y]
        mask_image = np.zeros((image.shape[0], image.shape[1]), np.uint8)
        mask_image = cv.circle(mask_image, rescaled_roi, self.radius, (255, 255, 255), -1)
        average_raw = cv.mean(image, mask=mask_image)[::-1]
        average = (int(average_raw[1]), int(average_raw[2]), int(average_raw[3]))
        return average

    def classify(self, image):
        rgb = self.roi_color(image)
        s = 0
        for i in range(0, 3):
            s += (self.empty_color[i] - rgb[i]) ** 2
        cv.putText(image, self.position, self.roi, cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv.LINE_AA)

    def get_zenith(self, depth_map, original_width, original_height) -> np.ndarray:
        width, height = depth_map.shape
        ratio_x, ratio_y = width / original_width, height / original_height
        contours = map(lambda x: (x[0] * ratio_x, x[1] * ratio_y), self.contour)
        edges = np.expand_dims(list(contours), axis=1).astype(np.int32) #vorher 1

        Scaling = True
        ###scaling edges/contours -> This can be helpful to prevent wrong pose estimation due to 
        #                            big chess pieces palced near smaller ones and therefor the zenith estimation
        #                            takes the wrong piece's height (overlapping -> see Intel Realsenseviewer)
        if Scaling == True:
            M = cv.moments(edges)
            cx = int(M['m10']/M['m00'])
            cy = int(M['m01']/M['m00'])
            cnt_norm = edges - [cx, cy]

            cnt_scaled = cnt_norm * 0.5 #Scaling Factor -> 0.5 still works fine

            cnt_scaled = cnt_scaled + [cx, cy]
            edges = cnt_scaled.astype(np.int32)
        ###end

        mask = np.zeros(depth_map.shape[:2]).astype(np.uint8)
        #cv.fillConvexPoly(mask, edges, 255, 1)
        cv.fillConvexPoly(mask, edges, 255, 1)
        extracted = np.zeros_like(depth_map)
        extracted[mask == 255] = depth_map[mask == 255]
        coords = np.where(extracted == np.amin(extracted[(mask==255) & (extracted>0)])) #added by thorben for corresponding image coords to depth
        x = coords[0][0]
        y = coords[1][0]
        return np.amin(extracted[(mask==255) & (extracted>0)]), x, y #changed by thorben - changed from np.amax to np.amin -> Highest point = lowest depth

    def __repr__(self):
        return str({'state': self.state, 'position': self.position, 'edges': [self.c1, self.c2, self.c3, self.c4]})

class ChessBoard:
    CHANGE_THRESHOLD = 35

    def __init__(self, fields: List[ChessBoardField], image, depth_map, chessboard_edges, scaling_factor_width, scaling_factor_height) -> None:
        self.fields = fields
        self.board_matrix = []
        self.promotion = 'q'
        self.promo = False
        self.move = ''
        self.image = image
        self.depth_map = depth_map
        self.chessboard_edge = chessboard_edges
        self.scaling_factor_width = scaling_factor_width
        self.scaling_factor_height = scaling_factor_height

    @property
    def edges(self):
        return self.chessboard_edge

    def total_detected_fields(self):
        return len(self.fields)

    def draw(self, image):
        for field in self.fields:
            field.draw(image, (0, 0, 255))

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

    def start(self):
        pieces = ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r']
        for i in range(8):
            self.fields[8*i + 0].state = pieces[i]
            self.fields[8*i + 1].state = 'p'
            self.fields[8*i + 2].state = '.'
            self.fields[8*i + 3].state = '.'
            self.fields[8*i + 4].state = '.'
            self.fields[8*i + 5].state = '.'
            self.fields[8*i + 6].state = 'P'
            self.fields[8*i + 7].state = pieces[i].upper()
        self.board_matrix.append([x.state for x in self.fields])

    def determine_changes(self, previous, current, width, height, current_play_color: str, debug=True, ):
        copy = current.copy()
        debug = False
        largest_field = 0
        second_largest_field = 0
        largest_dist = 0
        second_largest_dist = 0
        state_change = []
        for sq in self.fields:
            color_previous = sq.roi_color(previous, width, height)
            color_current = sq.roi_color(current, width, height)
            total = 0
            if sq.position in 'e2e4d2d4':
                print('test')
            for i in range(0, 3):
                total += (color_current[i] - color_previous[i]) ** 2
            distance = np.sqrt(total)
            if distance > 35:
                state_change.append(sq)
            if distance > largest_dist:
                second_largest_field = largest_field
                second_largest_dist = largest_dist
                largest_dist = distance
                largest_field = sq
            elif distance > second_largest_dist:
                # update second change in color
                second_largest_dist = distance
                second_largest_field = sq
        if len(state_change) == 2:
            field_one = largest_field
            field_two = second_largest_field
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
            if current_play_color == "w":
                if dist_curr1 < dist_curr2:
                    field_two.state = field_one.state
                    field_one.state = '.'
                    self.move = field_one.position + field_two.position
                else:
                    field_one.state = field_two.state
                    field_two.state = '.'
                    self.move = field_two.position + field_one.position
            else:
                if dist_curr1 < dist_curr2:
                    field_one.state = field_two.state
                    field_two.state = '.'
                    self.move = field_two.position + field_one.position
                else:
                    field_two.state = field_one.state
                    field_one.state = '.'
                    self.move = field_one.position + field_two.position

        else:
            # TODO: Implement Rochade / en passant
            raise RuntimeError(f'Invalid moves: {state_change}')
        return self.move

    @property
    def current_chess_matrix(self):
        matrix = []
        for i in range(8):
            matrix.append([])
            for j in range(8):
                matrix[i].append(self.fields[i + 8 * j].state)
        return matrix
