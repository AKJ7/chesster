__all__ = [
    'ChessBoard',
    'ChessBoardField'
]

import cv2 as cv
import numpy as np
from typing import List, Tuple


algebraic_notation = ['K', 'Q', 'B', 'N', 'R']
len_notation = {'white': ['K', 'Q', 'R', 'B', 'N', 'P'], 'black': ['k', 'q', 'r', 'b', 'n', 'p']}


class ChessBoardField:
    def __init__(self, image, c1: Tuple[float, float], c2, c3, c4, position: str, state=''):
        self.c1 = c1
        self.c2 = c2
        self.c3 = c3
        self.c4 = c4
        self.position = position
        self.contour = np.array([c1, c2, c4, c3], dtype=np.int32)
        center = cv.moments(self.contour)
        cx, cy = int(center['m10'] / center['m00']), int(center['m01'] / center['m00'])
        self.roi = (cx, cy)
        self.radius = 7
        self.empty_color = self.roi_color(image)
        self.state = state

    def draw(self, image, color, thickness=2):
        ctr = np.array(self.contour).reshape((-1, 1, 2)).astype(np.int32)
        cv.drawContours(image, [ctr], 0, color, thickness)

    def draw_roi(self, image, color, thickness=1):
        cv.circle(image, self.roi, self.radius, color, thickness)

    def roi_color(self, image):
        mask_image = np.zeros((image.shape[0], image.shape[1]), np.uint8)
        cv.circle(mask_image, self.roi, self.radius, (255, 255, 255), -1)
        average_raw = cv.mean(image, mask=mask_image)[::-1]
        average = (int(average_raw[1]), int(average_raw[2]), int(average_raw[3]))
        return average

    def classify(self, image):
        rgb = self.roi_color(image)
        s = 0
        for i in range(0, 3):
            s += (self.empty_color[i] - rgb[i]) ** 2
        cv.putText(image, self.position, self.roi, cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)


class ChessBoard:
    def __init__(self, fields: List[ChessBoardField]) -> None:
        self.fields = fields
        self.board_matrix = []
        self.promotion = 'q'
        self.promo = False
        self.move = ''

    def draw(self, image):
        for field in self.fields:
            field.draw(image, (0, 0, 255))

    def start(self):
        assert len(self.fields) == 64
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

    def get_changes_by_images(self, old_image, current_image):
        backup = current_image.copy()
        largest_square = 0
        second_largest_square = 0
        largest_dist = 0
        second_largest_dist = 0
        state_change = []
        for field in self.fields:
            color_previous = field.roi_color(old_image)
            color_current = field.roi_color(current_image)
            value = 0
            for i in range(3):
                value += (color_current[i] - color_previous[i]) ** 2
            distance = np.sqrt(value)
            if distance > 25:
                state_change.append(field)
            #TODO: Complete logic
