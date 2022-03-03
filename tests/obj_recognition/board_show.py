from chesster.obj_recognition.object_recognition import ObjectRecognition
import cv2 as cv
import os
import numpy as np
path = "C:/Mechatroniklabor/chesster/tests/obj_recognition/chessboard_data.pkl"
detector = ObjectRecognition(path, debug=True)

"""
img_previous = cv.imread("C:/Mechatroniklabor/chesster/previous.png")
img_current = cv.imread("C:/Mechatroniklabor/chesster/current.png")

detector.board.draw(img_current)

cv.imshow("Current IMG with ROI", img_current)
cv.waitKey(0)
"""
CImg = detector.board.image.copy()
#image = cv.cvtColor(CImg, cv.COLOR_BGR2HSV)
resized = cv.resize(CImg, (848, 480), interpolation = cv.INTER_CUBIC)
detector.board.draw_fields(resized)
cv.imshow("test",resized)
cv.imwrite('TestBild.png',resized)
cv.waitKey(0)