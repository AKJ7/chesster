from chesster.camera.realsense import RealSenseCamera
import cv2 as cv
from pathlib import Path
import time


if __name__ == '__main__':
    camera = RealSenseCamera()
    time.sleep(2)
    camera.capture_color()
    camera.capture_depth()
    time.sleep(2)
    file_time = time.strftime("%d_%m_%Y_%H_%M_%S")
    camera.save_color_capture(Path(f'{file_time}.jpg'))
    camera.save_depth_capture(Path(f'{file_time}'))
