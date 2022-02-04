from chesster.obj_recognition.object_recognition import ObjectRecognition
from chesster.camera.realsense import RealSenseCamera
import os
import time
camera = RealSenseCamera()
_ = camera.capture_color()
_, _ = camera.capture_depth()
time.sleep(1)
c_img = camera.capture_color()
d_img, _ = camera.capture_depth()
ObjectRecognition.create_chessboard_data(c_img, d_img, "C:/ChessterCalidata/Cali_0402.pkl")