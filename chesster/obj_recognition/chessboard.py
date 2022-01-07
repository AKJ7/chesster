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
        cv.putText(image, self.position, self.roi, cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv.LINE_AA)


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

    def save(self, path: Path):
        with open(path, 'wb') as dest:
            pickle.dump(self, dest)

    def get_corners(self):
        return [[x.c1, x.c2, x.c3, x.c4] for x in self.fields]

    @staticmethod
    def load(path: Path) -> ChessBoard:
        with open(path, 'rb') as src:
            board = pickle.load(src)
        return board

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

    def determine_changes(self, previous, current):
        copy = current.copy()
        debug = False
        largestSquare = 0
        secondLargestSquare = 0
        largestDist = 0
        secondLargestDist = 0
        stateChange = []
        for sq in self.fields:
            colorPrevious = sq.roi_color(previous)
            colorCurrent = sq.roi_color(current)
            sum = 0
            for i in range(0, 3):
                sum += (colorCurrent[i] - colorPrevious[i]) ** 2
            distance = np.sqrt(sum)
            if distance > 25:
                stateChange.append(sq)
            if distance > largestDist:
                secondLargestSquare = largestSquare
                secondLargestDist = largestDist
                largestDist = distance
                largestSquare = sq
            elif distance > secondLargestDist:
                # update second change in color
                secondLargestDist = distance
                secondLargestSquare = sq
        if len(stateChange) == 4:
            squareOne = stateChange[0]
            squareTwo = stateChange[1]
            squareThree = stateChange[2]
            squareFour = stateChange[3]
            if squareOne.position == 'e1' or squareTwo.position == 'e1' or squareThree.position == 'e1' or squareFour.position == 'e1':
                if squareOne.position == 'f1' or squareTwo.position == 'f1' or squareThree.position == 'f1' or squareFour.position == 'f1':
                    if squareOne.position == 'g1' or squareTwo.position == 'g1' or squareThree.position == 'g1' or squareFour.position == 'g1':
                        if squareOne.position == 'h1' or squareTwo.position == 'h1' or squareThree.position == 'h1' or squareFour.position == 'h1':
                            self.move = 'e1g1'
                            print(self.move)
                            if debug:
                                squareOne.draw(copy, (255, 0, 0), 2)
                                squareTwo.draw(copy, (255, 0, 0), 2)
                                squareThree.draw(copy, (255, 0, 0), 2)
                                squareFour.draw(copy, (255, 0, 0), 2)
                                cv.imshow('previous', previous)
                                cv.imshow('identified', copy)
                                cv.waitKey()
                                cv.destroyAllWindows()
                            return self.move
                if squareOne.position == 'd1' or squareTwo.position == 'd1' or squareThree.position == 'd1' or squareFour.position == 'd1':
                    if squareOne.position == 'c1' or squareTwo.position == 'c1' or squareThree.position == 'c1' or squareFour.position == 'c1':
                        if squareOne.position == 'a1' or squareTwo.position == 'a1' or squareThree.position == 'a1' or squareFour.position == 'a1':
                            self.move = 'e1c1'
                            print(self.move)
                            if debug:
                                squareOne.draw(copy, (255, 0, 0), 2)
                                squareTwo.draw(copy, (255, 0, 0), 2)
                                squareThree.draw(copy, (255, 0, 0), 2)
                                squareFour.draw(copy, (255, 0, 0), 2)
                                cv.imshow('previous', previous)
                                cv.imshow('identified', copy)
                                cv.waitKey()
                                cv.destroyAllWindows()
                            return self.move
            if squareOne.position == 'e8' or squareTwo.position == 'e8' or squareThree.position == 'e8' or squareFour.position == 'e8':
                if squareOne.position == 'f8' or squareTwo.position == 'f8' or squareThree.position == 'f8' or squareFour.position == 'f8':
                    if squareOne.position == 'g8' or squareTwo.position == 'g8' or squareThree.position == 'g8' or squareFour.position == 'g8':
                        if squareOne.position == 'h8' or squareTwo.position == 'h8' or squareThree.position == 'h8' or squareFour.position == 'h8':
                            self.move = 'e8g8'
                            print(self.move)
                            if debug:
                                squareOne.draw(copy, (255, 0, 0), 2)
                                squareTwo.draw(copy, (255, 0, 0), 2)
                                squareThree.draw(copy, (255, 0, 0), 2)
                                squareFour.draw(copy, (255, 0, 0), 2)
                                cv.imshow('previous', previous)
                                cv.imshow('identified', copy)
                                cv.waitKey()
                                cv.destroyAllWindows()
                            return self.move
                if squareOne.position == 'd8' or squareTwo.position == 'd8' or squareThree.position == 'd8' or squareFour.position == 'd8':
                    if squareOne.position == 'c8' or squareTwo.position == 'c8' or squareThree.position == 'c8' or squareFour.position == 'c8':
                        if squareOne.position == 'a8' or squareTwo.position == 'a8' or squareThree.position == 'a8' or squareFour.position == 'a8':
                            self.move = 'e8c8'
                            print(self.move)
                            if debug:
                                squareOne.draw(copy, (255, 0, 0), 2)
                                squareTwo.draw(copy, (255, 0, 0), 2)
                                squareThree.draw(copy, (255, 0, 0), 2)
                                squareFour.draw(copy, (255, 0, 0), 2)
                                cv.imshow('previous', previous)
                                cv.imshow('identified', copy)
                                cv.waitKey()
                                cv.destroyAllWindows()
                            return self.move
        squareOne = largestSquare
        squareTwo = secondLargestSquare
        if debug:
            squareOne.draw(copy, (255, 0, 0), 2)
            squareTwo.draw(copy, (255, 0, 0), 2)
            cv.imshow('previous', previous)
            cv.imshow('identified', copy)
            cv.waitKey(0)
            cv.destroyAllWindows()
        oneCurr = squareOne.roiColor(current)
        twoCurr = squareTwo.roiColor(current)
        sumCurr1 = 0
        sumCurr2 = 0
        for i in range(0, 3):
            sumCurr1 += (oneCurr[i] - squareOne.emptyColor[i]) ** 2
            sumCurr2 += (twoCurr[i] - squareTwo.emptyColor[i]) ** 2
        distCurr1 = np.sqrt(sumCurr1)
        distCurr2 = np.sqrt(sumCurr2)
        if distCurr1 < distCurr2:
            squareTwo.state = squareOne.state
            squareOne.state = '.'
            if squareTwo.state.lower() == 'p':
                if squareOne.position[1:2] == '2' and squareTwo.position[1:2] == '1':
                    self.promo = True
                if squareOne.position[1:2] == '7' and squareTwo.position[1:2] == '8':
                    self.promo = True
            self.move = squareOne.position + squareTwo.position
        else:
            squareOne.state = squareTwo.state
            squareTwo.state = '.'
            if squareOne.state.lower() == 'p':
                if squareOne.position[1:2] == '1' and squareTwo.position[1:2] == '2':
                    self.promo = True
                if squareOne.position[1:2] == '8' and squareTwo.position[1:2] == '7':
                    self.promo = True
            self.move = squareTwo.position + squareOne.position
        return self.move
