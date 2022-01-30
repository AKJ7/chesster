from chesster.camera.realsense import RealSenseCamera
import cv2 as cv
from pathlib import Path
import time


if __name__ == '__main__':
    with RealSenseCamera() as camera:
        file_time = time.strftime("%m_%d_%Y_%H_%M_%S")
        camera.save_color_capture(Path(f'{file_time}.jpg'))
        camera.save_depth_capture(Path(f'{file_time}'), False)
