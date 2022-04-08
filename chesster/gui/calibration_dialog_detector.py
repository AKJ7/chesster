
from turtle import update
from PyQt5.QtWidgets import QDialog
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QDialog, QLabel, QMessageBox
from chesster.gui.utils import get_ui_resource_path
from PyQt5 import QtGui
import os
from pathlib import Path
import numpy as np
import logging
import threading as th
from chesster.camera.realsense import RealSenseCamera
import time
from chesster.obj_recognition.object_recognition import ObjectRecognition
import cv2 as cv
logger = logging.getLogger(__name__)

class CalibrationDetector(QDialog):
    def __init__(self, flag_debug, parent=None):
        super(CalibrationDetector, self).__init__(parent)
        self.parent = parent
        self.flag_debug = flag_debug
        ui_path = get_ui_resource_path('calibration_dialog_detector.ui')
        loadUi(ui_path, self)
        self.label_img = QLabel()
        self.verticalLayout.addWidget(self.label_img)
        self.pushButton_main.clicked.connect(self.calibrate_T)
        self.pushButton_cycle_right.clicked.connect(lambda: self.cycle_debug_images(1))
        self.pushButton_cycle_left.clicked.connect(lambda: self.cycle_debug_images(-1))
        self.__camera = RealSenseCamera()   
        _ = self.__camera.capture_color()
        _, _ = self.__camera.capture_depth()
        if flag_debug==False:
            self.pushButton_cycle_left.setHidden(True)
            self.pushButton_cycle_right.setHidden(True)
        self.debug_images = []
        self.cycle_counter = 0
        self.label_status_main.setText('Press "Start" to start the calibration.')
        self.label_status_sub.setText('')
        
    def cycle_debug_images(self, direction):
        if self.cycle_counter == 0 and direction == -1:
            pass
        elif self.cycle_counter == len(self.debug_images)-1 and direction == 1:
            pass
        else:
            self.cycle_counter=self.cycle_counter + direction*1
        if len(self.debug_images)!=0:
            image = self.debug_images[self.cycle_counter]
            self.update_image(image, self.label_img)

    @staticmethod
    def update_image(image, image_label):
        Qtimage = QtGui.QImage(image.data, 848, 480, QtGui.QImage.Format_RGB888).rgbSwapped()
        image_label.clear()
        image_label.setPixmap(QtGui.QPixmap.fromImage(Qtimage))

    def calibrate_T(self):
        Thread = th.Thread(target=self.calibrate)
        Thread.start()

    def calibrate(self):
        self.debug_images = []
        self.pushButton_main.setEnabled(False)
        self.label_status_main.setText('Calibrating Chessboard/Detector data...')
        self.label_status_sub.setText('')
        c_img = self.__camera.capture_color()
        d_img, _ = self.__camera.capture_depth(apply_filter=True)
        #c_img = cv.imread('Testbild.png')
        #d_img = np.zeros((c_img.shape[0], c_img.shape[1]))
        self.debug_images.append(c_img.copy())
        self.update_image(self.debug_images[0], self.label_img)

        board = ObjectRecognition.create_chessboard_data(c_img.copy(), d_img, Path(os.environ['CALIBRATION_DATA_PATH']), debug=False)
        classify_image = c_img.copy()
        board.draw_fields(classify_image)
        self.debug_images.append(classify_image)
        print(len(self.debug_images))
        n_fields = board.total_detected_fields()
        if n_fields == 64:
            self.label_status_main.setText('Calibration successful! You may close this window now.')
        else:
            self.label_status_main.setText(f'Calibration failed. {n_fields} fields detected.')
            self.label_status_sub.setText('Please press "try again". If this error occures again, move the board a little bit or refer to the documentation.')
        self.pushButton_main.setText('Try again')
        self.pushButton_main.setEnabled(True)
