
from PyQt5.QtWidgets import QDialog
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QDialog, QLabel, QMessageBox
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from chesster.gui.utils import get_ui_resource_path
from PyQt5 import QtGui
from chesster.moduls.GenericSysFunctions import ImportCSV
from chesster.vision_based_control.controller import VBC_Calibration, LogCallback
from chesster.Robot.UR10 import UR10Robot
from chesster.camera.realsense import RealSenseCamera
from chesster.moduls.ImageProcessing import HSV_Color_Selector
import os
from pathlib import Path
import numpy as np
import logging
import threading as th
import time
logger = logging.getLogger(__name__)

class Calibration_vbc(QDialog):
    def __init__(self, save_img = False, tcp_check = False, n_data = 5000, skip_data_generation = False, parent = None):
        super(Calibration_vbc, self).__init__(parent)
        self.parent = parent
        ui_path = get_ui_resource_path('calibration_dialog_vbc.ui')
        loadUi(ui_path, self)
        self.save_img = save_img
        self.tcp_check = tcp_check
        self.n_data = n_data
        self.skip_data_generation = skip_data_generation
        self.VBC_Calibration = VBC_Calibration()
        self.VBC_Calibration.start()
        self.random_sample = self.VBC_Calibration.PointGeneration(self.n_data)
        self.image_frame = QLabel()
        self.gridLayout_image.addWidget(self.image_frame)
        self.message_box = QMessageBox(self)
        self.message_box.windowTitleChanged.connect(self.show_notify)
        self.adjust_b = self.message_box.addButton('Adjust', QMessageBox.NoRole)
        self.continue_b = self.message_box.addButton('Continue', QMessageBox.NoRole)
        self.create_graph()
        self.create_NN_Graph()
        self.create_benchmark_graph()
        self.LogCallback = LogCallback(self.figNN, self.axes1NN, self.axes2NN, self.label_status_sub)
        self.progressBar_training.setHidden(True)
        self.lineEdit_progressbar.setHidden(True)
        self.progressBar_training.setValue(0)
        self.lineEdit_progressbar.textChanged.connect(self.update_progressbar)
        if self.tcp_check:
            self.label_status.setText('Checkup for calibrated colors due. Press "Start" to begin.')
            self.pushButton_Main.clicked.connect(self.perform_tcp_checkupT)
        else:
            self.label_status.setText('Press "Start" to begin the training procedure.')
            self.pushButton_Main.clicked.connect(self.training_procedureT)
        self.label_status_sub.setText('')

    def update_image(self, image, label):
        Qtimage = QtGui.QImage(image.data, image.shape[1], image.shape[0], QtGui.QImage.Format_RGB888).rgbSwapped()
        label.setPixmap(QtGui.QPixmap.fromImage(Qtimage))

    def perform_tcp_checkup(self):
        self.original_imgs, processed_imgs = self.VBC_Calibration.TCPDetectionCheck(self.random_sample)
        self.update_image(processed_imgs, self.image_frame)
        self.set_notify(msg='Please choose whether you want to adjust the color thresholds or continue with the current settings.', title='TCP Detection Checkup')
    
    def perform_tcp_checkupT(self):
        Thread = th.Thread(target=self.perform_tcp_checkup)
        Thread.start()

    def training_procedure(self):
        self.pushButton_Main.setHidden(True)
        if self.skip_data_generation:
            #Skipping data generation and using data in directory
            self.label_status.setText('Reading data from resources/VBC_Data/...')
            self.label_status_sub.setText('Reading training_data_Input.csv...')
            X_filtered = ImportCSV(Path(os.environ['NEURAL_NETWORK_DATA_PATH']), 'training_data_Input.csv', ';')
            self.label_status_sub.setText('Reading training_data_Output.csv...')
            Y_filtered = ImportCSV(Path(os.environ['NEURAL_NETWORK_DATA_PATH']), 'training_data_Output.csv', ';')
            self.label_status_sub.setText('Plotting Data...')
            self.axes3.scatter(X_filtered[0,:], X_filtered[1,:], X_filtered[2,:], c=X_filtered[2,:], marker='o', cmap=cm.jet, edgecolors='0.2', lw=0.4, s=30)
            self.axes4.scatter(Y_filtered[0,:], Y_filtered[1,:], Y_filtered[2,:], c=X_filtered[2,:], marker='o', cmap=cm.jet, edgecolors='0.2', lw=0.4, s=30)
        else:
            self.label_status.setText(f'Generating {self.n_data} training pairs...')
            X, Y, X_filtered, Y_filtered = self.VBC_Calibration.GenerateTrainingdata(self.random_sample, self.update_image,
                                                        self.n_data, [self.label_status, self.label_status_sub, self.progressBar_training, self.lineEdit_progressbar, self.image_frame], self.save_img)

            self.label_status_sub.setText('Plotting Data...')
            self.axes1.scatter(X[0,:], X[1,:], X[2,:], c='red', marker='o')
            self.axes2.scatter(Y[0,:], Y[1,:], Y[2,:], c='red', marker='o')
            self.axes3.scatter(X_filtered[0,:], X_filtered[1,:], X_filtered[2,:], c=X_filtered[2,:], marker='o', cmap=cm.jet, edgecolors='0.2', lw=0.4, s=30)
            self.axes4.scatter(Y_filtered[0,:], Y_filtered[1,:], Y_filtered[2,:], c=X_filtered[2,:], marker='o', cmap=cm.jet, edgecolors='0.2', lw=0.4, s=30)

        self.gridLayout_image.removeWidget(self.image_frame)
        self.image_frame.deleteLater()
        self.image_frame=None
        self.gridLayout_image.addWidget(self.canvas)

        for i in range(10):
            self.label_status_sub.setText(f'Continueing in {10-i}s...')
            time.sleep(1)
        self.label_status.setText(f'Training the neural network model...')
        self.gridLayout_image.removeWidget(self.canvas)
        for axes in self.axes:
            axes.clear()
        self.fig.clear()
        self.canvas.draw()
        self.canvas = None
        plt.close(self.fig)

        self.gridLayout_image.addWidget(self.canvasNN)
        Err_data = self.VBC_Calibration.TrainNeuralNetwork(X_filtered, Y_filtered, self.LogCallback)
        self.label_status.setText('Training done. Showing benchmark results..')
        self.label_status_sub.setText('')
        time.sleep(2)
        self.gridLayout_image.removeWidget(self.canvasNN)
        self.figNN.clear()
        self.canvasNN.draw()
        self.canvasNN = None
        plt.close(self.figNN)

        self.gridLayout_image.addWidget(self.canvasBenchmark)
        x_bar = np.arange(2)
        y_bar = [x + 0.3 for x in x_bar]
        self.axesBenchmark.bar(x_bar, [Err_data[0],Err_data[2]], width = 0.3, color = '#6EBF8B', label='error <= 3mm')
        self.axesBenchmark.bar(y_bar, [Err_data[1],Err_data[3]], width = 0.3, color = '#D82148', label='error <= 5mm')
        self.axesBenchmark.set_xticks([r+0.15 for r in range(2)], ['x-coordinate', 'y-coordinate'])
        self.axesBenchmark.legend(loc="upper right")
        self.axesBenchmark.bar_label(self.axesBenchmark.containers[0])
        self.axesBenchmark.bar_label(self.axesBenchmark.containers[1])
        self.axesBenchmark.set_ylim(0, 105)
        self.canvasBenchmark.draw()

        for i in range(60):
            self.label_status_sub.setText(f'Shutting down in {60-i}s...')
            time.sleep(1)
            
        super(Calibration_vbc, self).close()

    def training_procedureT(self):
        Thread = th.Thread(target=self.training_procedure)
        Thread.start()

    def set_notify(self, msg = '', title = ''):
        self.message_box.setText(msg)   
        self.message_box.setWindowTitle(title)

    def show_notify(self):
        _ = self.message_box.exec()
        if self.message_box.clickedButton() == self.adjust_b:
            self.VBC_Calibration.color_upper_limit, self.VBC_Calibration.color_lower_limit = HSV_Color_Selector(self.original_imgs)
        else:
            pass
        self.message_box = QMessageBox(self)
        self.message_box.windowTitleChanged.connect(self.show_notify)
        self.pushButton_Main.clicked.disconnect()
        self.pushButton_Main.clicked.connect(self.training_procedureT)
        self.pushButton_Main.setText('Next Step')
        self.label_status.setText('TCP Detection Checkup done. Please press "Next Step" to begin the training procedure.')
        
    def create_graph(self):
        self.fig = Figure()
        self.fig.patch.set_alpha(0.0)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setStyleSheet("background-color:transparent;")
        self.axes1 = self.fig.add_subplot(221, projection='3d')
        self.axes1.patch.set_alpha(0.0)
        self.axes1.set_title(f'Raw Data Input')
        self.axes1.set_xlabel('x [px]')
        self.axes1.set_ylabel('y [px]')
        self.axes1.set_zlabel('Depth [mm]')

        self.axes2 = self.fig.add_subplot(222, projection='3d')
        self.axes2.patch.set_alpha(0.0)
        self.axes2.set_title(f'Raw Output')
        self.axes2.set_xlabel('X Robot KOS [mm]')
        self.axes2.set_ylabel('Y Robot KOS [mm]')
        self.axes2.set_zlabel('Z Robot KOS [mm]')
        
        self.axes3 = self.fig.add_subplot(223, projection='3d')
        self.axes3.patch.set_alpha(0.0)
        self.axes3.set_title(f'Filtered Input')
        self.axes3.set_xlabel('x [px]')
        self.axes3.set_ylabel('y [px]')
        self.axes3.set_zlabel('Depth [mm]')

        self.axes4 = self.fig.add_subplot(224, projection='3d')
        self.axes4.patch.set_alpha(0.0)
        self.axes4.set_title(f'Filtered Output')
        self.axes4.set_xlabel('X Robot KOS [mm]')
        self.axes4.set_ylabel('Y Robot KOS [mm]')
        self.axes4.set_zlabel('Z Robot KOS [mm]')

        self.fig.tight_layout()
        self.axes = [self.axes1, self.axes2, self.axes3, self.axes4]

    def create_NN_Graph(self):
        self.figNN = Figure()
        self.figNN.patch.set_alpha(0.0)
        self.canvasNN = FigureCanvas(self.figNN)
        self.canvasNN.setStyleSheet("background-color:transparent;")

        self.axes1NN = self.figNN.add_subplot(211)
        self.axes1NN.patch.set_alpha(0.0)
        self.axes1NN.set_title(f'Neural Network accuracy')
        self.axes1NN.set_xlabel('epochs')
        self.axes1NN.set_ylabel('accuracy')
        self.axes1NN.grid(linestyle = '--', linewidth = 0.3)
        self.axes2NN = self.figNN.add_subplot(212)
        self.axes2NN.patch.set_alpha(0.0)
        self.axes2NN.set_title(f'Neural Network loss [mae]')
        self.axes2NN.set_xlabel('epochs')
        self.axes2NN.set_ylabel('loss')
        self.axes2NN.grid(linestyle = '--', linewidth = 0.3)

        self.figNN.tight_layout()

    def create_benchmark_graph(self):
        self.figBenchmark = Figure()
        self.canvasBenchmark = FigureCanvas(self.figBenchmark)
        self.canvasBenchmark.setStyleSheet("background-color:transparent;")
        self.axesBenchmark = self.figBenchmark.add_subplot(111)
        self.axesBenchmark.patch.set_alpha(0.0)
        self.axesBenchmark.set_title(f'Neural network benchmark (n=100)')
        self.axesBenchmark.set_xlabel('Tolerances')
        self.axesBenchmark.set_ylabel('No. of entrys')
        #self.axesBenchmark.grid()

    def update_progressbar(self):
        self.progressBar_training.setValue(int(self.lineEdit_progressbar.text()))