import numpy as np
import sys as sys
import os as os
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.callbacks import TensorBoard
from tensorflow import keras
sys.path.append(os.path.dirname(sys.path[0])) #preperation for import of custom moduls
from moduls.GenericSysFunctions import Printtimer, ImportCSV, ExportCSV, ChooseFolder #Import of custom moduls
from moduls.ImageProcessing import ExtractImageCoordinates
from camera.realSense import RealSenseCamera
from Robot.UR10 import UR10Robot
import cv2 as cv

Robot = None
model = None
c_img=[]
d_img=[]

def onmouse(event, x, y, flags, param):
    global c_img, d_img, model, Robot
    if event == cv.EVENT_LBUTTONDOWN:
        x_old_ptp = 1035.0 #CURRENTLY HARDCODED
        x_old_min = 40.0
        y_old_ptp = 1120.9
        y_old_min = -897.0
        pos = (x,y)
        Input = np.array([x, y, d_img[x,y]])
        Input = Input[np.newaxis, :]
        Input = 2.*(Input - x_old_min)/x_old_ptp-1 #normalization
        print(Input)
        print(Input.shape)
        cv.circle(c_img, (x,y), 3, [0, 0, 255], -1)
        cv.putText(c_img, f"IMG CORDS: x:{x} - y:{y} - depth:{d_img[x,y]}", (x-40, y-20), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        #Input = np.array([1.280000000000000000e+02, 3.180000000000000000e+02, 1.019000000000000000e+03])
        #Input = Input[np.newaxis, :]
        prediction = model.predict(Input)
        #prediction = np.round(prediction, decimals=2)
        prediction = ((prediction+1)*y_old_ptp)/2+y_old_min
        prediction = np.round(prediction, 2)
        print(prediction)

        cv.putText(c_img, f"PREDICTION: x:{prediction[0, 0]} - y:{prediction[0, 1]} - z:{prediction[0, 2]}", (x-40, y-60), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        cv.imshow("Img", c_img)

        ORIENTATION = np.array([0,-3.143, 0]) #Standard Orientation for Grasping
        #ORIENTATION = np.array([0, 2.220, -2.220]) #Standard Orientation for Grasping
        Pose_offset = np.array([prediction[0, 0], prediction[0, 1], 100, ORIENTATION[0], ORIENTATION[1], ORIENTATION[2]])

        Robot.MoveC(Pose_offset)
        print(Robot.WhereC())

def main():
    global c_img, d_img, model, Robot
    Robot = UR10Robot()
    TRAINING_HOME_Init = np.array([0, -120, 120, 0, -90, -180]) #has to be called because the robot will otherwise crash into the camera
    TRAINING_HOME = np.array([60, -120, 120, 0, 90, 180])
    Robot.MoveJ(TRAINING_HOME_Init)
    Robot.MoveJ(TRAINING_HOME)
    
    NAME = "nD5_nN40_nData200_nEpochs200"
    NAME = "TEST_FLAT"
    model = keras.models.load_model("C:/NN/"+NAME)
    Camera = RealSenseCamera()  
    while True:
        cv.destroyAllWindows
        cv.namedWindow("Img",1)
        cv.setMouseCallback("Img", onmouse)

        c_img = Camera.capture_color()
        d_img = Camera.capture_depth()

        cv.imshow("Img", c_img)
        cv.waitKey(0)
    

if __name__ == "__main__":
    main()