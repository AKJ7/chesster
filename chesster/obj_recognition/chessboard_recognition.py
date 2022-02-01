__all__ = [
    'ChessboardRecognition'
]

import cv2 as cv
from matplotlib import pyplot as plt
import numpy as np
from chesster.obj_recognition.chessboard import *
import imutils as im
import logging
from typing import List, Tuple
from pathlib import Path
#from chesster.obj_recognition.utils import KMeansCluster
from collections import defaultdict

logger = logging.getLogger(__name__)


class Line:
    def __init__(self, x1, y1, x2, y2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

    def grows(self) -> bool:
        return abs(self.x2 - self.x1) > abs(self.y2 - self.y1)

    def get_angle(self) -> float:
        if self.x1 == self.x2 and self.y1 == self.y2:
            return 0
        return np.deg2rad(90) if np.isclose(self.x2, self.x1) else np.arctan((self.y2 - self.y1) / (self.x2 - self.x1))

    def find_intersection(self, rhs):
        x = ((self.x1 * self.y2 - self.y1 * self.x2) * (rhs.x1 - rhs.x2) - (self.x1 - self.x2) * (
                rhs.x1 * rhs.y2 - rhs.y1 * rhs.x2)) / (
                    (self.x1 - self.x2) * (rhs.y1 - rhs.y2) - (self.y1 - self.y2) * (rhs.x1 - rhs.x2))
        y = ((self.x1 * self.y2 - self.y1 * self.x2) * (rhs.y1 - rhs.y2) - (self.y1 - self.y2) * (
                rhs.x1 * rhs.y2 - rhs.y1 * rhs.x2)) / (
                    (self.x1 - self.x2) * (rhs.y1 - rhs.y2) - (self.y1 - self.y2) * (rhs.x1 - rhs.x2))
        return int(x), int(y)

    def __repr__(self):
        return str({'x1': self.x1, 'y1': self.y1, 'x2': self.x2, 'y2': self.y2})


class ChessboardRecognition:
    DEFAULT_IMAGE_SIZE = (400, 400)

    @staticmethod
    def from_image(image, *, depth_map=None, debug=False) -> ChessBoard:
        original_image = image.copy()
        adaptive_thresh, image = ChessboardRecognition.__normalize_image(image, debug)
        mask, chessboard_edge = ChessboardRecognition.__initialize_mask(adaptive_thresh, image, debug)
        trans_image, trans_matrix = ChessboardRecognition.__get_transformed_image(image, chessboard_edge, debug)
        edges, color_edges = ChessboardRecognition.__find_edges(trans_image, debug)
        horizontal_lines, vertical_lines = ChessboardRecognition.__find_lines(edges, color_edges, trans_image, debug)
        corners = ChessboardRecognition.__find_corners(horizontal_lines, vertical_lines, color_edges, debug)
        fields = ChessboardRecognition.__find_fields(corners, color_edges, debug)
        transformed_fields = ChessboardRecognition.__get_retransformed_image(color_edges, trans_matrix, *image.shape[:2], fields, debug=debug)
        extracted_map = None
        if depth_map is not None:
            width, height = original_image.shape[:2]
            rescaled_width, rescaled_height = image.shape[:2]
            scale_width, scale_height = width / rescaled_width, height / rescaled_height
            rescaled_chessboard_edges = list(map(lambda x: np.ceil([x[0] * scale_width, x[1] * scale_height]), chessboard_edge))
            extracted_map = ChessboardRecognition.__extract_depth(depth_map, rescaled_chessboard_edges, debug=True)
        return ChessBoard(transformed_fields, image, extracted_map, chessboard_edge)

    @staticmethod
    def __normalize_image(image, debug=False):
        image = ChessboardRecognition.__unsharp_mask(image)
        img = im.resize(image, width=ChessboardRecognition.DEFAULT_IMAGE_SIZE[0], height=ChessboardRecognition.DEFAULT_IMAGE_SIZE[1])
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        adaptive_threshold = cv.adaptiveThreshold(gray, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY, 125, 1)
        ChessboardRecognition.__auto_debug(debug, adaptive_threshold, None, title='Adaptive Threshold', cmap='gray')
        return adaptive_threshold, img

    @staticmethod
    def __initialize_mask(adaptive_thresh, image, debug=False):
        contours, hierarchy = cv.findContours(adaptive_thresh, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
        img_contours = image.copy()
        largest_ratio = largest_area = largest_perimeter = 0
        largest = None
        largest_index = -1
        for index in range(len(contours)):
            area = cv.contourArea(contours[index])
            perimeter = cv.arcLength(contours[index], True)
            if perimeter > 0:
                ratio = area / perimeter
                if ratio > largest_ratio:
                    largest = contours[index]
                    largest_ratio = ratio
                    largest_perimeter = perimeter
                    largest_area = area
                    largest_index = index
        cv.drawContours(img_contours, [largest], -1, (0, 255, 255), 1)
        epsilon = 0.05 * largest_perimeter
        chessboard_edge = cv.approxPolyDP(largest, epsilon, True)
        mask = np.zeros(image.shape[:2]).astype(np.uint8) * 128
        cv.fillConvexPoly(mask, chessboard_edge, 255, 1)
        extracted = np.zeros_like(image)
        extracted[mask == 255] = image[mask == 255]
        extracted[np.where((extracted == [125, 125, 125]).all(axis=2))] = [0, 0, 20]
        chessboard_edge = np.array(chessboard_edge).astype(np.float32).squeeze()
        ChessboardRecognition.__auto_debug(debug, extracted, None, title='Extracted Mask', cmap='gray')
        return extracted, chessboard_edge

    @staticmethod
    def __get_transformed_image(image, chessboard_edge, debug=False):
        width, height = image.shape[:2]
        transformation_matrix = cv.getPerspectiveTransform(chessboard_edge, np.array([[0, 0], [width, 0],
            [width, height], [0, height]]).astype(np.float32))
        wrapped_image = cv.warpPerspective(image, transformation_matrix, (width, height))
        ChessboardRecognition.__auto_debug(debug, wrapped_image, title='')
        return wrapped_image, transformation_matrix

    @staticmethod
    def __find_edges(image, debug=False):
        gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
        edges = cv.Canny(gray, 70, 150)
        color_edges = cv.cvtColor(edges, cv.COLOR_GRAY2BGR)
        ChessboardRecognition.__auto_debug(debug, edges, None, title='', cmap='gray')
        return edges, color_edges

    @staticmethod
    def __find_lines(edges, color_edges, image, debug=False):
        lines = cv.HoughLines(edges, 1, np.pi / 360, 70, None, 0, 0)
        horizontal_lines = []
        vertical_lines = []
        copy = image.copy()
        for l in lines:
            rho, theta = l[0][0], l[0][1]
            a, b = np.cos(theta), np.sin(theta)
            x0, y0 = a * rho, b * rho
            pt1, pt2 = (int(x0 + 1000 * -b), int(y0 + 1000 * a)), (int(x0 - 1000 * -b), int(y0 - 1000 * a))
            cv.line(copy, pt1, pt2, (255, 0, 0), 2)
            line = Line(*pt1, *pt2)
            horizontal_lines.append(line) if line.grows() else vertical_lines.append(line)
        ChessboardRecognition.__auto_debug(debug, copy, title='Lines')
        return horizontal_lines, vertical_lines

    @staticmethod
    def __find_corners(horizontal_lines: List[Line], vertical_lines, color_edges, debug=False):
        corners = []
        for h in horizontal_lines:
            for v in vertical_lines:
                x1, x2 = h.find_intersection(v)
                corners.append([x1, x2])
        dedupe_corners = []
        for c in corners:
            matching_flag = False
            for d in dedupe_corners:
                if np.sqrt((d[0]-c[0])*(d[0]-c[0]) + (d[1]-c[1])*(d[1]-c[1])) < 15:
                    matching_flag = True
                    break
            if not matching_flag:
                dedupe_corners.append(c)
        for d in dedupe_corners:
            cv.circle(color_edges, (d[0], d[1]), 5, (0, 0, 225))
        ChessboardRecognition.__auto_debug(debug, color_edges)
        return dedupe_corners

    @staticmethod
    def __find_fields(corners: List[Tuple[float, float]], color_edges, debug=False):
        corners.sort(key=lambda x: x[1])
        rows = []
        for corner in corners:
            matching_flag = False
            for r in rows:
                if abs(r - corner[1]) < 13:
                    matching_flag = True
                    break
            if not matching_flag:
                rows.append(corner[1])
        fields = {}
        for corner in corners:
            for r in rows:
                if abs(corner[1] - r) < 13:
                    fields.setdefault(r, [])
                    fields[r].append(corner)
        rows = fields.values()
        for r in rows:
            r.sort(key=lambda x: x[0])
        rows = [r for r in rows]
        letters = ''.join([chr(a) for a in range(97, 123)])
        numbers = [f'{a}' for a in range(1, 26)]
        fields = []
        for r in range(len(rows) - 1): #-1
            for c in range(len(rows[0]) - 1):# -1
                try:
                    c1 = rows[r][c]
                    c2 = rows[r][c+1]
                    c3 = rows[r+1][c]
                    c4 = rows[r+1][c+1]
                    # TODO: Flip on color change
                    position = f'{letters[r]}{numbers[c]}'
                    new_field = ChessBoardField(color_edges, c1, c2, c3, c4, position)
                    new_field.draw(color_edges, (255, 0, 0), 2)
                    new_field.draw_roi(color_edges, (255, 0, 0), 2)
                    new_field.classify(color_edges)
                    fields.append(new_field)
                except Exception as e:
                    print(e, r, c, f'rows: {len(rows)}', f'cols: {len(rows[0])}')
        ChessboardRecognition.__auto_debug(debug, color_edges)
        return fields

    @staticmethod
    def __get_retransformed_image(image, transformation_matrix, width, height, fields: List[ChessBoardField], debug=False):
        inverse_transform = np.linalg.inv(transformation_matrix)
        unwrapped = cv.warpPerspective(image, inverse_transform, (height, width))
        ret = []
        for field in fields:
            c1, c2, c3, c4 = cv.perspectiveTransform(np.array([[field.c1, field.c2, field.c3, field.c4]]).astype(np.float32), inverse_transform).squeeze()
            new_field = ChessBoardField(unwrapped, c1, c2, c4, c3, field.position)
            new_field.draw(unwrapped, (0, 255, 0), 2)
            new_field.draw_roi(unwrapped, (0, 255, 0), 2)
            ret.append(new_field)
        ChessboardRecognition.__auto_debug(debug, unwrapped)
        return ret

    @staticmethod
    def __unsharp_mask(image, kernel_size=(5, 5), sigma=1.0, amount=7.0, threshold=0):
        blurred = cv.GaussianBlur(image, kernel_size, sigma)
        sharpened = float(amount + 1) * image - float(amount) * blurred
        sharpened = np.maximum(sharpened, np.zeros(sharpened.shape))
        sharpened = np.minimum(sharpened, 255 * np.ones(sharpened.shape))
        sharpened = sharpened.round().astype(np.uint8)
        if threshold > 0:
            low_contrast_mask = np.absolute(image - blurred) < threshold
            np.copyto(sharpened, image, where=low_contrast_mask)
        return sharpened

    @staticmethod
    def __extract_depth(depth_map, edges, debug=False):
        edges = np.expand_dims(edges, axis=1).astype(np.int32)
        mask = np.zeros(depth_map.shape[:2]).astype(np.uint8)
        cv.fillConvexPoly(mask, edges, 255, 1)
        extracted = np.zeros_like(depth_map)
        extracted[mask == 255] = depth_map[mask == 255]
        np.save('extracted', extracted)
        if debug:
            ChessboardRecognition.__plot_3d_map(extracted)
        return extracted

    @staticmethod
    def __auto_debug(debug, img, color_map=cv.COLOR_BGR2RGB, title=None, **kwargs):
        if debug:
            ChessboardRecognition.__debug_plot(img, color_map=color_map, title=title, **kwargs)

    @staticmethod
    def __debug_plot(img, color_map, title, **kwargs):
        plt.axis('off')
        if title is not None:
            plt.title(title)
        plt.imshow(img if color_map is None else cv.cvtColor(img, color_map), **kwargs)
        plt.show()

    @staticmethod
    def __plot_3d_map(depth_image):
        plt.axis('off')
        width, height = depth_image.shape
        fig = plt.figure()
        ax = fig.add_subplot(projection='3d')
        ax.invert_zaxis()
        data = depth_image.flatten()
        X = np.transpose(np.meshgrid(range(width), range(height), indexing='ij'), (1, 2, 0)).reshape(-1, 2)
        c = np.abs(data)
        cmhot = plt.get_cmap('hot')
        plt.scatter(X.T[0], X.T[1], data, c=c, cmap=cmhot)
        plt.show()