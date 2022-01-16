import sys 
import os
sys.path.append(os.path.dirname(sys.path[0])) #preperation for import of custom moduls
from camera.realSense import RealSenseCamera
import cv2
RealSense = RealSenseCamera()
global img
7
def onmouse(event, x, y, flags, param):
    global img, d_img, model, Robot
    if event == cv2.EVENT_LBUTTONDOWN:
        cv2.putText(img, f"x {x}, y {y}", (x-20, y-20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        cv2.imshow("CAP",img)
        cv2.waitKey(0)
while True:
    
    img, frame = RealSense.capture_depth()
    img = RealSense.hole_filling(frame)
    depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(img, alpha=15), cv2.COLORMAP_JET)
    cv2.waitKey(500)
    cv2.imshow("RS", depth_colormap)
    cv2.setMouseCallback("RS", onmouse)
    cv2.waitKey(500) #I added this to play with timings, thought it might help - didn't.

