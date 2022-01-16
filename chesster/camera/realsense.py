import pyrealsense2 as rs
import numpy as np
import cv2 as cv
from pathlib import Path
from typing import Optional
from chesster.master.module import Module


class RealSenseCamera(Module):
    def __init__(self, width: int = 848, height: int = 480, frame_rate: int = 30, require_rbg=True, auto_start=True):
        self.__pipeline = rs.pipeline()
        self.__config = rs.config()
        self.__pipeline_wrapper = rs.pipeline_wrapper(self.__pipeline)
        self.__pipeline_profile = self.__config.resolve(self.__pipeline_wrapper)
        self.__device = self.__pipeline_profile.get_device()
        rgb_found = False
        for s in self.__device.sensors:
            if s.get_info(rs.camera_info.name) == 'RGB Camera':
                rgb_found = True
                break
        if not rgb_found and require_rbg:
            raise RuntimeError('No Realsense Camera with color sensor detected!')
        self.__config.enable_stream(rs.stream.color, width, height, rs.format.bgr8, frame_rate)
        self.__config.enable_stream(rs.stream.depth, width, height, rs.format.z16, frame_rate)
        align_to = rs.stream.color
        self.__align = rs.align(align_to)
        self.__hole_filling = rs.hole_filling_filter()
        if auto_start:
            self.__start()

    def __repr__(self):
        return f'<{self.get_device_name()}>'

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__stop()
        return self

    def __start(self):
        self.__pipeline.start(self.__config)

    def __stop(self):
        self.__pipeline.stop()

    def start(self):
        self.__start()

    def stop(self):
        self.__stop()

    def get_device_product_line(self) -> str:
        return self.__device.get_info(rs.camera_info.product_line)

    def get_device_name(self) -> str:
        return self.__device.get_info(rs.camera_info.name)

    def get_device_serial_number(self) -> str:
        return self.__device.get_info(rs.camera_info.serial_number)

    def get_device_id(self) -> str:
        return self.__device.get_info(rs.camera_info.product_id)

    def capture(self, timeout_ms=5000):
        return self.__pipeline.wait_for_frames(timeout_ms=timeout_ms)

    def capture_color(self) -> Optional[np.ndarray]:
        ret = self.capture()
        frame = ret.get_color_frame()
        if not frame:
            return None
        return np.asanyarray(frame.get_data())

    def capture_depth(self) -> Optional[np.ndarray]:
        ret = self.capture()
        aligned_frames = self.__align.process(ret)
        aligned_depth_frame = aligned_frames.get_depth_frame()
        if not aligned_depth_frame:
            return None
        depth_img = np.asanyarray(aligned_depth_frame.get_data())
        return depth_img, aligned_depth_frame

    def fill_holes(self, depth_img) -> Optional[np.ndarray]:
        processed_Depth_frame = self.__hole_filling.process(depth_img)
        processed_Depth = np.asanyarray(processed_Depth_frame.get_data())
        return processed_Depth

    def save_color_capture(self, path: Path) -> bool:
        img = self.capture_color()
        if img is None:
            return False
        cv.imwrite(str(path.absolute()), img)
        return True
    
    def save_depth_capture(self, path: Path) -> bool:
        img = self.capture_depth()
        if img is not None:
            np.save(str(path), img)
            return True
        return False

    # def __del__(self):
    #     self.__pipeline.stop()
