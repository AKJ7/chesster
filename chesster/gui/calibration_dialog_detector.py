import os
import matplotlib
matplotlib.use('module://chesster.gui.my_backend')
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QDialog, QLabel, QSizePolicy
from chesster.gui.utils import get_ui_resource_path
from PyQt5 import QtGui
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QRunnable, QThreadPool, Qt
from pathlib import Path
from PyQt5.QtGui import QPixmap
import logging
from chesster.obj_recognition.chessboard_recognition import ChessboardRecognition
from chesster.camera.realsense import RealSenseCamera
import numpy as np
from matplotlib.figure import Figure
from chesster.gui import image_plot_signal
from PIL import ImageQt, Image
from io import StringIO, BytesIO

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
    plot_signal = pyqtSignal(object)

    def __init__(self, parent=None):
        super(CalibrationDetector, self).__init__(parent)
        self.parent = parent
        ui_path = get_ui_resource_path('calibration_dialog_detector.ui')
        loadUi(ui_path, self)
        self.connect_signal_events()
        self.__camera = RealSenseCamera()
        self.__camera.capture_color()
        self.__camera.capture_depth()
        self.figures = []
        logger.info('Started Object recognition Calibrator!')

    def connect_signal_events(self):
        self.actionCalibrate.triggered.connect(self.calibrate)
        image_plot_signal.connect(self.plot_images)

    @staticmethod
    def update_image(image: np.ndarray, image_label):
        width, height, depth = image.shape
        image = QtGui.QImage(image.data, width, height, QtGui.QImage.Format_BGR888)
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
        for i in reversed(range(self.scrollAreaContents.count())):
            item = self.scrollAreaContents.itemAt(i)
            if item.widget() is not None:
                widget = item.widget()
                self.scrollAreaContents.removeWidget(widget)
        pool = QThreadPool.globalInstance()
        current_image = self.__camera.capture_color()
        current_depth_image, _ = self.__camera.capture_depth(apply_filter=True)
        runnable = Calibrate(self.disable_button, self.enable_button, current_image, current_depth_image)
        pool.start(runnable)

    def plot_images(self, number, figure: Figure):
        fig = figure
        buff = BytesIO()
        fig.savefig(buff)
        buff.seek(0)
        image = Image.open(buff)
        qt_image = ImageQt.ImageQt(image)
        pix = QPixmap.fromImage(qt_image)
        label = QLabel()
        label.setPixmap(pix)
        label.adjustSize()
        label.setScaledContents(True)
        label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)
        self.scrollAreaContents.addWidget(label)
