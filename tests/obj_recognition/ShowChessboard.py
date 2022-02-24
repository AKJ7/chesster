from chesster.obj_recognition.object_recognition import ObjectRecognition
import cv2 as cv
import os

path = "C:/Mechatroniklabor/chesster/chesster/resources/CalibrationData/chessboard_data.pkl"
detector = ObjectRecognition(path)

img_previous = cv.imread("C:/Mechatroniklabor/chesster/previous.png")
img_current = cv.imread("C:/Mechatroniklabor/chesster/current.png")

detector.board.draw(img_current)

cv.imshow("Current IMG with ROI", img_current)
cv.waitKey(0)