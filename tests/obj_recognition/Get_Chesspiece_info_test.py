from xml.etree.ElementTree import ProcessingInstruction
from chesster.obj_recognition.object_recognition import ObjectRecognition
import cv2 as cv
import os
import numpy as np
import pickle as pk
import numpy as np
def process_debug_image(debug_image, detector):
    new_coords = []
    for i in range(len(detector.dumped_coords[0])):
        new_coords.append([detector.dumped_coords[0][i], detector.dumped_coords[1][i]])
    for coords in new_coords:
        x = coords[0]
        y = coords[1]
        print(f'X: {x}, Y: {y}')
        cv.circle(debug_image, (y,x), 2, (0,0,255), -1)
    return debug_image

path = "C:/Mechatroniklabor/chesster/tests/obj_recognition/chessboard_data.pkl"
detector = ObjectRecognition(path)

depth_img_current = np.load("C:/Mechatroniklabor/chesster/tests/camera/03_03_2022_17_47_08.npy")
depth_img_previous = np.load("C:/Mechatroniklabor/chesster/tests/camera/03_03_2022_17_47_26.npy")
depth_colormap = cv.applyColorMap(cv.convertScaleAbs(depth_img_current, alpha=15), cv.COLORMAP_JET)
color_img_current = cv.imread("C:/Mechatroniklabor/chesster/tests/camera/03_03_2022_17_47_08.jpg")
color_img_previous = cv.imread("C:/Mechatroniklabor/chesster/tests/camera/03_03_2022_17_47_26.jpg")

detector.get_chesspiece_info('b1', depth_img_current)

debug_img = process_debug_image(color_img_current, detector)

cv.imshow('Debug', debug_img)
cv.waitKey(0)