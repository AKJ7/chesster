import numpy as np
import cv2 as cv


class ChessPiece:
    def __init__(self, position, coordinate, zenith):
        self.position = position
        self.coordinate = coordinate
        self.zenith = zenith
