import cv2 as cv
import numpy as np
import imutils as imutils

img = cv.imread("chesster\Vision-Based-Control\Testbilder\Figur 1.jpg")
img = cv.resize(img, (1280,1024))
gs = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

circles_mask = np.zeros(gs.shape, dtype=np.uint8)
circles = cv.HoughCircles(gs, cv.HOUGH_GRADIENT, 1.5, 20)

circles = np.round(circles[0, :]).astype("int")
for (x, y, r) in circles:
    cv.circle(gs, (x,y), r, (0, 255, 0), 2)

cv.imshow("Edges", gs)
cv.imshow("image with ColorDetection", gs)
cv.waitKey(0)
cv.destroyAllWindows()
