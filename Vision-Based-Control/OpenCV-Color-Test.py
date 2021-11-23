import cv2 as cv
import numpy as np
import imutils as imutils

img = cv.imread("Vision-Based-Control/Testfigur sehr weit.jpg")
img = cv.resize(img, (1280,1024))
hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)

co = np.array([178, 130, 82])
cobgr = np.array([82, 130, 178])
color_orange = np.array([30,54,70])
lower_range = np.array([15,100,20])
upper_range = np.array([25,255,255])

mask = cv.inRange(hsv, lower_range, upper_range)

#cv.imshow("Circles", img)
cv.imshow("Mask", mask)
# cv.waitKey(0)
# cv.destroyAllWindows()

cnts = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
cnts = imutils.grab_contours(cnts)
used_cnts = cnts.copy()
i=0
for c in cnts:
    M = cv.moments(c)
    area = cv.contourArea(c)
    if(area>=20.0):
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])
        print(f"Centerpoint {i} painted")
        cv.drawContours(img, [c], -1, [50, 168, 80], 2)
        cv.circle(img, (cX,cY), 3, [50, 168, 80], -1)
        cv.putText(img, "center", (cX-20, cY-20), cv.FONT_HERSHEY_SIMPLEX, 0.5, (50, 168, 80), 2)
            
    else:
        pass
        i=i+1

cv.imshow("image with ColorDetection", img)
cv.waitKey(0)
cv.destroyAllWindows()
