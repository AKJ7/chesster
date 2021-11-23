import cv2 as cv
import numpy as np

img = cv.imread("Vision-Based-Control/circles.png")
hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)

lower_range = np.array([110, 50, 50])
upper_range = np.array([130, 255, 255])

mask = cv.inRange(hsv, lower_range, upper_range)

cv.imshow("Circles", img)
cv.imshow("Mask", mask)
# cv.waitKey(0)
# cv.destroyAllWindows()

cnts = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

cv.imshow("cnts", cnts)
cv.waitKey(0)
cv.destroyAllWindows()
