__all__ = [
    'ChessBoardRecognition'
]

import logging

import cv2 as cv
import numpy as np
import imutils as im
from dataclasses import dataclass
from chesster.obj_recognition.chessboard import ChessBoard, ChessBoardField
from matplotlib import pyplot as plt


class Line:
    def __init__(self, x1, y1, x2, y2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

    def grows(self) -> bool:
        return abs(self.x2 - self.x1) > abs(self.y2 - self.y1)

    def find_intersection(self, rhs):
        x = ((self.x1 * self.y2 - self.y1 * self.x2) * (rhs.x1 - rhs.x2) - (self.x1 - self.x2) * (
                    rhs.x1 * rhs.y2 - rhs.y1 * rhs.x2)) / (
                        (self.x1 - self.x2) * (rhs.y1 - rhs.y2) - (self.y1 - self.y2) * (rhs.x1 - rhs.x2))
        y = ((self.x1 * self.y2 - self.y1 * self.x2) * (rhs.y1 - rhs.y2) - (self.y1 - self.y2) * (
                    rhs.x1 * rhs.y2 - rhs.y1 * rhs.x2)) / (
                        (self.x1 - self.x2) * (rhs.y1 - rhs.y2) - (self.y1 - self.y2) * (rhs.x1 - rhs.x2))
        return int(x), int(y)


class ChessBoardRecognition:
    DEFAULT_IMAGE_SIZE = (400, 400)

    @staticmethod
    def from_image(image, debug=False) -> ChessBoard:
        ChessBoardRecognition.__auto_debug(debug, image)
        adaptive_thresh, img = ChessBoardRecognition.__normalize_image(image, debug)
        mask = ChessBoardRecognition.__initialize_mask(adaptive_thresh, img, debug)
        edges, color_edges = ChessBoardRecognition.__find_edges(mask, debug)
        horizontal_lines, vertical_lines = ChessBoardRecognition.__find_lines(edges, color_edges, img, debug)
        corners = ChessBoardRecognition.__find_corners(horizontal_lines, vertical_lines, color_edges, debug)
        fields = ChessBoardRecognition.__find_squares(corners, img, debug)
        return ChessBoard(fields)

    @staticmethod
    def __normalize_image(img, debug=False):
        img = im.resize(img, width=ChessBoardRecognition.DEFAULT_IMAGE_SIZE[0],
                        height=ChessBoardRecognition.DEFAULT_IMAGE_SIZE[0])
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        adaptive_thresh = cv.adaptiveThreshold(gray, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY, 125, 1)
        ChessBoardRecognition.__auto_debug(debug, adaptive_thresh, None, cmap='gray')
        return adaptive_thresh, img

    @staticmethod
    def __initialize_mask(adaptive_thresh, img, debug=False):
        contours, hierarchy = cv.findContours(adaptive_thresh, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
        img_contours = img.copy()
        largest_ratio = 0
        largest_area = 0
        largest_perimeter = 0
        largest = 0
        for index in range(len(contours)):
            area = cv.contourArea(contours[index])
            perimeter = cv.arcLength(contours[index], True)
            if index == 0:
                largest_ratio = 0
            if perimeter > 0:
                ratio = area / perimeter
                if ratio > largest_ratio:
                    largest = contours[index]
                    largest_ratio = ratio
                    largest_perimeter = perimeter
                    largest_area = area
        cv.drawContours(img_contours, [largest], -1, (0, 0, 0), 1)
        # epsilon = 0.05 * largest_perimeter
        epsilon = 0
        chessboard_edge = cv.approxPolyDP(largest, epsilon, True)
        mask = np.zeros((img.shape[0], img.shape[1]), 'uint8') * 128
        cv.fillConvexPoly(mask, chessboard_edge, 255, 1)
        extracted = np.zeros_like(img)
        extracted[mask == 255] = img[mask == 255]
        extracted[np.where((extracted == [125, 125, 125]).all(axis=2))] = [0, 0, 20]
        ChessBoardRecognition.__auto_debug(debug, extracted, None, cmap='gray')
        return extracted

    @staticmethod
    def __find_edges(mask, debug=False):
        edges = cv.Canny(mask, 70, 200)
        color_edges = cv.cvtColor(edges, cv.COLOR_GRAY2BGR)
        ChessBoardRecognition.__auto_debug(debug, edges, None, cmap='gray')
        return edges, color_edges

    @staticmethod
    def __find_lines(edges, color_edges, img, debug=False):
        lines = cv.HoughLines(edges, 1, np.pi / 180, 70, np.array([]), 0, 0)
        horizontal_lines = []
        vertical_lines = []
        for index in range(0, len(lines)):
            rho = lines[index][0][0]
            theta = lines[index][0][1]
            a, b = np.cos(theta), np.sin(theta)
            x0, y0 = a * rho, b * rho
            pt1, pt2 = (int(x0 + 1000 * -b), int(y0 + 1000 * a)), (int(x0 - 1000 * -b), int(y0 - 1000 * a))
            cv.line(img, pt1, pt2, (255, 0, 0), 3)
            line = Line(*pt1, *pt2)
            horizontal_lines.append(line) if line.grows() else vertical_lines.append(line)
        ChessBoardRecognition.__auto_debug(debug, img)
        return horizontal_lines, vertical_lines

    @staticmethod
    def __find_corners(horizontal_lines, vertical_lines, color_edge, debug=False):
        corners = []
        for h in horizontal_lines:
            for v in vertical_lines:
                x1, x2 = h.find_intersection(v)
                corners.append([x1, x2])
        dedupe_corners = []
        for c in corners:
            matching_flag = False
            for d in dedupe_corners:
                if np.sqrt((d[0]-c[0])*(d[0]-c[0]) + (d[1]-c[1])*(d[1]-c[1])) < 10:
                    matching_flag = True
                    break
            if not matching_flag:
                dedupe_corners.append(c)
        for d in dedupe_corners:
            cv.circle(color_edge, (d[0], d[1]), 10, (0, 0, 225))
        ChessBoardRecognition.__auto_debug(debug, color_edge)
        return dedupe_corners

    @staticmethod
    def __find_squares(corners, color_edges, debug=False):
        corners.sort(key=lambda x: x[0])
        rows = [[], [], [], [], [], [], [], [], []]
        r = 0
        for c in range(0, min(81, len(corners))):
            if c > 0 and c % 9 == 0:
                if r > len(rows):
                    logging.warning(f'More rows found ({c // 9}) than allowed ({len(rows)})!')
                    continue
                r += 1
            rows[r].append(corners[c])
        letters = ''.join([chr(a) for a in range(97, 123)])
        numbers = [f'{a}' for a in range(0, 26)]
        squares = []
        for r in rows:
            r.sort(key=lambda y: y[1])
        for r in range(0, 8):
            for c in range(0, 8):
                c1 = rows[r][c]
                c2 = rows[r][c+1]
                c3 = rows[r+1][c]
                c4 = rows[r+1][c+1]
                position = f'{letters[r]}{numbers[7-c]}'
                new_square = ChessBoardField(color_edges, c1, c2, c3, c4, position)
                new_square.draw(color_edges, (255, 0, 0), 2)
                new_square.draw_roi(color_edges, (255, 0, 0), 2)
                new_square.classify(color_edges)
                squares.append(new_square)
        ChessBoardRecognition.__auto_debug(debug, color_edges)
        return squares

    @staticmethod
    def __auto_debug(debug, img, color_map=cv.COLOR_BGR2RGB, axis=False, **kwargs):
        if debug:
            ChessBoardRecognition.__debug_plot(img, color_map=color_map, axis=axis, **kwargs)

    @staticmethod
    def __debug_plot(img, color_map=cv.COLOR_BGR2RGB, axis=False, **kwargs):
        if not axis:
            plt.axis('off')
        plt.imshow(img if color_map is None else cv.cvtColor(img, color_map), **kwargs)
        plt.show()
