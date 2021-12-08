import pyrealsense2 as rs
import numpy as np
import cv2 as cv
from pathlib import Path


class RealSenseCamera:
    def __init__(self, width: int = 640, height: int = 480, frame_rate: int = 30, require_rbg=True):
        self.__pipeline = rs.pipeline()
        self.__config = rs.config()
        self.__pipeline_wrapper = rs.pipeline_wrapper(self.__pipeline)
        self.__pipeline_profile = self.__config.resolve(self.__pipeline_wrapper)
        self.__device = self.__pipeline_profile.get_device()
        rgb_found = False
        if require_rbg:
            for s in self.__device.sensors:
                if s.get_info(rs.camera_info.name) == 'RGB Camera':
                    rgb_found = True
                    break
        if not rgb_found:
            # Exception in Constructor ...
            raise RuntimeError('No Realsense Camera with color sensor detected!')
        self.__config.enable_stream(rs.stream.color, width, height, rs.format.bgr8, frame_rate)
        self.__start()

    def __repr__(self):
        return f'<{self.get_device_name()}>'

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __start(self):
        self.__pipeline.start(self.__config)

    def stop(self):
        self.__pipeline.stop()

    def get_device_product_line(self) -> str:
        return self.__device.get_info(rs.camera_info.product_line)

    def get_device_name(self) -> str:
        return self.__device.get_info(rs.camera_info.name)

    def get_device_serial_number(self) -> str:
        return self.__device.get_info(rs.camera_info.serial_number)

    def get_device_id(self) -> str:
        return self.__device.get_info(rs.camera_info.product_id)

    def capture(self, timeout_ms=50000):
        return self.__pipeline.wait_for_frames(timeout_ms=timeout_ms)

    def capture_color(self):
        ret = self.capture()
        frame = ret.get_color_frame()
        if not frame:
            return None
        return np.asanyarray(frame.get_data())

    def save_color_capture(self, path: Path) -> bool:
        img = self.capture_color()
        if not img:
            return False
        cv.imwrite(path, img)
        return True

    def __del__(self):
        self.__pipeline.stop()
