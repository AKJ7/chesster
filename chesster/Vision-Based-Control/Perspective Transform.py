import numpy as np
import cv2 as cv
import glob
import time
import sys
import os
sys.path.append(os.path.dirname(sys.path[0])) #preperation for import of custom moduls
from camera.realSense import RealSenseCamera
points = list()
def onmouse(event, x, y, flags, param):
    global c_img, points
    if event == cv.EVENT_LBUTTONDOWN:
        cv.circle(c_img, (x,y), 5, color=(0, 0, 255))
        points.append([x, y])
    if len(points) == 4:
        pts1 = np.float32([points[0],points[1],points[2],points[3]])
        pts2 = np.float32([[0,0],[500,0],[0,400],[500,400]])
        M = cv.getPerspectiveTransform(pts1,pts2)
        print(M)
        dst = cv.warpPerspective(c_img,M,(500,400))
        cv.imshow("transformed img", dst)

        img_2 = cv.imread("C:/Users/admin/Desktop/ML/chesster/chesster/Vision-Based-Control/Trainingsdaten/Images3000/ImageC 67.bmp")
        img_2 = cv.warpPerspective(img_2, M,(500,400))
        cv.imshow('Test', img_2)

camera = RealSenseCamera()
c_img = camera.capture_color()
time.sleep(1)
c_img = camera.capture_color()
cv.namedWindow("Img",1)
cv.setMouseCallback("Img", onmouse)
while True:
    cv.imshow("Img", c_img)
    cv.waitKey(5)