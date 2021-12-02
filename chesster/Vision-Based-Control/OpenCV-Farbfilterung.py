import cv2 as cv
import numpy as np
import imutils as imutils

img = cv.imread("Vision-Based-Control\Testbilder\Zwei Figuren Mittel.jpg")
img = cv.resize(img, (1280,1024))
hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)

color_orange_name = "Springer"
color_orange = np.array([30,54,70])
co_lower_range = np.array([20/2,100,40])
co_upper_range = np.array([45/2,255,255])

color_green_name = "Läufer"
color_green = np.array([90/2,30,70])
cg_lower_range = np.array([75/2,30,20])
cg_upper_range = np.array([160/2,255,255])

color_corresponds = np.array([color_orange_name, color_green_name])
colors = list()
colors.append([color_orange, co_lower_range, co_upper_range])
colors.append([color_green, cg_lower_range, cg_upper_range])
masks = list([])
for i in range(len(colors)):
    masks.append(cv.inRange(hsv, colors[i][1], colors[i][2]))

mask = cv.inRange(hsv, co_lower_range, co_upper_range)
cnts_all = list([])
i=0
for mask in masks:
    cv.imshow(f"Mask {i}", mask)
    cnts = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    cnts_all.append(imutils.grab_contours(cnts))
    i=i+1

i=0
for j in range(len(colors)):
    for c in cnts_all[j]:
        M = cv.moments(c)
        area = cv.contourArea(c)
        if(area>=20.0):
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            print(f"Centerpoint {i} painted")
            cv.drawContours(img, [c], -1, [360, 90, 47], 2)
            cv.circle(img, (cX,cY), 3, [360, 90, 47], -1)
            cv.putText(img, f"{color_corresponds[j]}", (cX-20, cY-20), cv.FONT_HERSHEY_SIMPLEX, 0.5, (360, 90, 47), 2)
                
        else:
            pass
            i=i+1

cv.imshow("image with ColorDetection", img)
cv.waitKey(0)
cv.destroyAllWindows()
