from PyQt5.QtWidgets import QDialog
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QDialog, QLabel, QGroupBox, QRadioButton
from chesster.gui.utils import get_ui_resource_path
from chesster.gui.calibration_dialog_vbc import Calibration_vbc
from chesster.gui.calibration_dialog_detector import CalibrationDetector
import logging

logger = logging.getLogger(__name__)


class Calibration(QDialog):
    def __init__(self, parent=None):
        super(Calibration, self).__init__(parent)
        self.parent = parent
        ui_path = get_ui_resource_path('calibration_dialog.ui')
        loadUi(ui_path, self)
        self.vbc_elements = [self.label_vbc_1, self.input_no_trainingdata, self.checkBox_vbc_savedata, self.checkBox_vbc_calibratecolor,
                                self.label_vbc_2, self.label_vbc_time, self.label_vbc_4, self.checkBox_vbc_skip]
        self.input_no_trainingdata.textChanged.connect(self.update_vbc_time)
        self.checkBox_vbc.toggled.connect(lambda: self.update_layout('vbc'))
        self.checkBox_detector.toggled.connect(lambda: self.update_layout('detector'))
        self.checkBox_vbc_skip.toggled.connect(self.update_data_label)
        self.pushButton_start.clicked.connect(self.start_calibration)
        self.label_usedata.setHidden(True)
        self.toggle_vbc(True)
        self.update_vbc_time()

    def update_layout(self, flag):
        if flag=='vbc' and self.checkBox_vbc.isChecked():
            self.toggle_vbc(False)
            self.checkBox_detector.toggled.disconnect()
            self.checkBox_detector.setChecked(False)
            self.checkBox_detector.toggled.connect(lambda: self.update_layout('detector'))
            self.pushButton_start.setEnabled(True)
        elif flag == 'detector' and self.checkBox_detector.isChecked():
            self.toggle_vbc(True)
            self.checkBox_vbc.toggled.disconnect()
            self.checkBox_vbc.setChecked(False)
            self.checkBox_vbc.toggled.connect(lambda: self.update_layout('vbc'))
            self.pushButton_start.setEnabled(True)
        else:
            self.toggle_vbc(True)
            self.pushButton_start.setEnabled(False)

    def update_data_label(self):
        if self.checkBox_vbc_skip.isChecked():
            self.label_usedata.setHidden(False)
        else:
            self.label_usedata.setHidden(True)

    def update_vbc_time(self):
        try:
            n = int(self.input_no_trainingdata.text())
        except Exception:
            self.label_vbc_time.setText('NAN. Please enter an integer')
        else:
            self.label_vbc_time.setText(f'~ {round(n/21, 1)} minutes')

    def toggle_vbc(self, hide=False):
        for element in self.vbc_elements:
            element.setHidden(hide)

    def start_calibration(self):
        if self.checkBox_vbc.isChecked():
            CaliVBC = Calibration_vbc(self.checkBox_vbc_savedata.isChecked(), self.checkBox_vbc_calibratecolor.isChecked(),
                                int(self.input_no_trainingdata.text()), self.checkBox_vbc_skip.isChecked(), parent=self.parent)
            CaliVBC.show()
        else:
            detector_calibration = CalibrationDetector(self.parent)
            detector_calibration.show()
        self.close()
