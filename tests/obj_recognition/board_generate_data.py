from chesster.obj_recognition.object_recognition import ObjectRecognition
from chesster.camera.realsense import RealSenseCamera
from pathlib import Path
import time
import logging

logging.basicConfig(level=logging.INFO)

if __name__ == '__main__':
    camera = RealSenseCamera()
    camera.capture_color()
    camera.capture_depth()
    time.sleep(1)
    c_img = camera.capture_color()
    d_img, _ = camera.capture_depth()
    board = ObjectRecognition.create_chessboard_data(c_img, d_img, Path('../../chesster/resources/CalibrationData/chessboard_data.pkl'), debug=True)
