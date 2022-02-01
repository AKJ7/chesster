from chesster.obj_recognition.object_recognition import ObjectRecognition
from chesster.camera.realsense import RealSenseCamera
import os
camera = RealSenseCamera()
c_img = camera.capture_color()
d_img, _ = camera.capture_depth()
ObjectRecognition.create_chessboard_data(c_img, d_img, "C:/Chesster/test2.pkl")