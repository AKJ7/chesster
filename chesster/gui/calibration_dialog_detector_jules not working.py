import os
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QDialog, QLabel, QMessageBox, QPushButton
from chesster.gui.utils import get_ui_resource_path
from PyQt5 import QtGui
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QThread, QObject, QRunnable, QThreadPool, Qt
from pathlib import Path
import logging
import threading as th
from chesster.obj_recognition.chessboard_recognition import ChessboardRecognition
from chesster.camera.realsense import RealSenseCamera
import numpy as np

logger = logging.getLogger(__name__)


class Calibrate(QRunnable):
    def __init__(self, on_start, on_stop, image, depth_data):
        super(Calibrate, self).__init__()
        self.on_start = on_start
        self.on_stop = on_stop
        self.image = image
        self.depth_data = depth_data

    def run(self):
        logger.info('Calibration started!')
        self.on_start()
        try:
            detector = ChessboardRecognition.from_image(self.image, depth_map=self.depth_data, debug=True)
            detector.save(Path(os.environ.get('CALIBRATION_DATA_PATH')))
        except Exception as e:
            logger.exception(e)
        self.on_stop()
        logger.info('Calibration ended!')


class CalibrationDetector(QDialog):
    def __init__(self, parent=None):
        super(CalibrationDetector, self).__init__(parent)
        self.parent = parent
        ui_path = get_ui_resource_path('calibration_dialog_detector.ui')
        loadUi(ui_path, self)
        self.connect_signal_events()
        self.__camera = RealSenseCamera()
        self.__camera.capture_color()
        self.__camera.capture_depth()
        logger.info('Started Object recognition Calibrator!')

    def connect_signal_events(self):
        self.actionCalibrate.triggered.connect(self.calibrate)

    @staticmethod
    def update_image(image: np.ndarray, image_label):
        width, height, depth = image.shape
        image = QtGui.QImage(image.data, width, height, QtGui.QImage.Format_RGB888).rgbSwapped()
        image_label.clear()
        image_label.setPixmap(QtGui.QPixmap.fromImage(image))

    @pyqtSlot()
    def disable_button(self) -> None:
        self.pushButton.setEnabled(False)
        self.pushButton.setFlat(True)

    @pyqtSlot()
    def enable_button(self) -> None:
        self.pushButton.setEnabled(True)
        self.pushButton.setFlat(False)

    def calibrate(self):
        pool = QThreadPool.globalInstance()
        current_image = self.__camera.capture_color()
        current_depth_image, _ = self.__camera.capture_depth(apply_filter=True)
        runnable = Calibrate(self.disable_button, self.enable_button, current_image, current_depth_image)
        pool.start(runnable)
