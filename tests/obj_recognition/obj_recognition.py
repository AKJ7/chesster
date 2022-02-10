from chesster.obj_recognition.object_recognition import *
import cv2 as cv
import matplotlib
from matplotlib import pyplot as plt
matplotlib.use('TkAgg')

# image = cv.imread('../camera/img/01_27_2022_15_41_54.jpg')
image = cv.imread('img/2021-12-23-183320_2.jpg')

ObjectRecognition.create_chessboard_data(image, None, Path('chessboard_data.pkl'), True)


detector = ObjectRecognition('chessboard_data.pkl', True)
detector.start('w')
fields = detector.get_fields()
print(fields)
detector.get_board_visual()

