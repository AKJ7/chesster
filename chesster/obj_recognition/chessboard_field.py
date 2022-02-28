import numpy as np
from typing import Tuple
import cv2 as cv


class ChessBoardField:
    def __init__(self, image, c1: Tuple[float, float], c2, c4, c3, position: str, state=''):
        self.c1 = c1
        self.c2 = c2
        self.c3 = c3
        self.c4 = c4
        self.position = position
        self.contour = np.array([c1, c2, c3, c4], dtype=np.int32)
        center = cv.moments(self.contour)
        cx, cy = int(center['m10'] / center['m00']), int(center['m01'] / center['m00'])
        self.roi = (cx, cy)
        self.radius = 10
        self.shape = image.shape
        self.empty_color = self.roi_color(image)
        self.state = state

    @property
    def col(self):
        return self.position[0]

    @property
    def row(self):
        return int(self.position[1])

    @property
    def piece(self):
        return self.state

    def draw(self, image, color=None, thickness=1, scale_contour=False):
        width, height = image.shape[:2]
        ratio_x, ratio_y = self.get_ratio(width, height)
        contours = map(lambda x: (x[0] * ratio_x, x[1] * ratio_y), self.contour)
        ctr = np.array(list(contours)).reshape((-1, 1, 2)).astype(np.int32)
        if scale_contour:
            M = cv.moments(ctr)
            cx = int(M['m10']/M['m00'])
            cy = int(M['m01']/M['m00'])
            cnt_norm = ctr - [cx, cy]
            cnt_scaled = cnt_norm * 0.4
            cnt_scaled = cnt_scaled + [cx, cy]
            ctr = cnt_scaled.astype(np.int32)
        if color is None:
            cv.drawContours(image, [ctr], 0, self.empty_color, cv.FILLED)
        else:
            cv.drawContours(image, [ctr], 0, color, thickness)

    def draw_roi(self, image, color, thickness=1):
        width, height = image.shape[:2]
        ratio_x, ratio_y = self.get_ratio(width, height)
        rescaled_roi_x = int(self.roi[0] * ratio_x)
        rescaled_roi_y = int(self.roi[1] * ratio_y)
        rescaled_roi = (rescaled_roi_x, rescaled_roi_y)
        cv.circle(image, rescaled_roi, self.radius, color, thickness)

    def roi_color(self, image):
        width, height = image.shape[:2]
        ratio_x, ratio_y = self.get_ratio(width, height)
        rescaled_roi_x = int(self.roi[0] * ratio_x)
        rescaled_roi_y = int(self.roi[1] * ratio_y)
        rescaled_roi = (rescaled_roi_x, rescaled_roi_y)
        mask_image = np.zeros((image.shape[0], image.shape[1]), np.uint8)
        mask_image = cv.circle(mask_image, rescaled_roi, self.radius, (255, 255, 255), -1)
        average_raw = cv.mean(image, mask=mask_image)[::-1]
        average = (int(average_raw[1]), int(average_raw[2]), int(average_raw[3]))
        return average

    def classify(self, image, color=(255, 0, 255)):
        rgb = self.roi_color(image)
        s = 0
        for i in range(0, 3):
            s += (self.empty_color[i] - rgb[i]) ** 2
        cv.putText(image, self.position, self.roi, cv.FONT_HERSHEY_SIMPLEX, 0.3, color, 1, cv.LINE_AA)

    def get_zenith(self, depth_map, scale_contours=True):
        width, height = depth_map.shape
        ratio_x, ratio_y = self.get_ratio(width, height)
        contours = map(lambda x: (x[0] * ratio_x, x[1] * ratio_y), self.contour)
        edges = np.expand_dims(list(contours), axis=1).astype(np.int32)
        if scale_contours:
            M = cv.moments(edges)
            cx = int(M['m10']/M['m00'])
            cy = int(M['m01']/M['m00'])
            cnt_norm = edges - [cx, cy]
            cnt_scaled = cnt_norm * 0.4
            cnt_scaled = cnt_scaled + [cx, cy]
            edges = cnt_scaled.astype(np.int32)
        mask = np.zeros(depth_map.shape[:2]).astype(np.uint8)
        cv.fillConvexPoly(mask, edges, 255, 1)
        extracted = np.zeros_like(depth_map)
        extracted[mask == 255] = depth_map[mask == 255]
        coords = np.where(extracted == np.amin(extracted[(mask == 255) & (extracted > 0)]))
        x = coords[0][0]
        y = coords[1][0]
        return np.amin(extracted[(mask == 255) & (extracted > 0)]), x, y

    def get_ratio(self, current_width, current_height):
        return current_width / self.shape[0], current_height / self.shape[1]

    def __repr__(self):
        return str({'state': self.state, 'pos': self.position})
