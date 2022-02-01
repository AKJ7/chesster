import numpy as np
import cv2 as cv


class ChessPiece:
    def __init__(self, position, coordinate, zenith, x, y):
        self.position = position
        self.coordinate = coordinate
        self.zenith = zenith
        self.y_cimg = y #row
        self.x_cimg = x #col