from chesster.camera.realsense import RealSenseCamera
from matplotlib import pyplot as plt
import cv2 as cv


# Smoke test

camera = RealSenseCamera()
img = camera.capture_color()
assert img is not None
cv.cvtColor(img, cv.COLOR_BGR2GRAY)
cv.imshow('image', img)
cv.waitKey(0)
cv.destroyAllWindows()
