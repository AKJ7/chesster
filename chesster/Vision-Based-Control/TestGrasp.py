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
from camera.realsense import RealSenseCamera
from Robot.UR10 import UR10Robot
import cv2 as cv
from sklearn.preprocessing import MinMaxScaler, StandardScaler
import threading as th
import time
Robot = None
model = None
c_img=[]
proc_d_img=[]
State=0
r_img = np.zeros((480, 848, 3))
n=0

def lin_reg_result(X, Y, coeff = np.array([1.06015269e+03, -5.94343938e-01, -1.89386788e-01])):
    Z = coeff[1]*X+coeff[2]*Y+coeff[0]
    return Z

def nothing(x):
    pass

def get_Data(n_out, n_in, Norm=1, Fixed_height=True, XName="Input389Filtered.csv", YName="Output389Filtered.csv"):
    DIRPATH = os.path.dirname(__file__)
    Dir = DIRPATH+"/Trainingsdaten/"
    X = ImportCSV(Dir, XName, ";")
    X = np.round(X, 3)
    Y = ImportCSV(Dir, YName, ";")
    Y = np.round(Y, 3)
    X = np.transpose(X)
    Y = np.transpose(Y)
    print(X[-50,:])
    
    if Fixed_height == True:
        Y[:,2] = 120
    if Norm == 1:  
        #Normalization between -1 and 1
        scalerX = MinMaxScaler(feature_range=(-1,1))
        scalerX.fit(X[:, 0:n_in])
        X_Norm = scalerX.transform(X[:, 0:n_in])
        scalerY = MinMaxScaler(feature_range=(-1,1))
        scalerY.fit(Y[:, 0:n_out])
        Y_Norm = scalerY.transform(Y[:, 0:n_out])
    elif Norm == 2:
        #Normalization between 0 and 1
        scalerX = MinMaxScaler()
        scalerX.fit(X[:, 0:n_in])
        X_Norm = scalerX.transform(X[:, 0:n_in])
        scalerY = MinMaxScaler()
        scalerY.fit(Y[:, 0:n_out])
        Y_Norm = scalerY.transform(Y[:, 0:n_out])
    elif Norm == 3:
        scalerX = StandardScaler()
        scalerX.fit(X[:, 0:n_in])
        X_Norm = scalerX.transform(X[:, 0:n_in])
        scalerY = MinMaxScaler()
        scalerY.fit(Y[:, 0:n_out])
        Y_Norm = scalerY.transform(Y[:, 0:n_out])
    else: 
        X_Norm = X
        Y_Norm = Y
        scalerY = None
        scalerX = None

    return X_Norm, Y_Norm, X, Y, scalerX, scalerY

def onmouseT(event, x, y, flags, param):
    thread = th.Thread(target=onmouse, args=(event, x, y, flags, param))
    thread.start()

def onmouse(event, x, y, flags, param):
    global c_img, proc_d_img, model, Robot, State, r_img, n
    if event == cv.EVENT_LBUTTONDOWN:
        if n==0:
            n=n+1
        else:
            s = cv.getTrackbarPos('Sliding:' ,'Img')
            
            if proc_d_img[y,x] != 0:
                Input = np.array([x, y, proc_d_img[y,x]]) #Flipped!
                Input = Input.astype(float)  
                Input = Input[np.newaxis, :]
                r_img = c_img.copy()
                print(f'raw Input: {Input}')
                _, _, _, _, scalerX, scalerY = get_Data(2, 3, Norm=1, Fixed_height=False, XName="Input4119Filtered_newData.csv", YName="Output4119Filtered_newData.csv")
                Input = scalerX.transform(Input)
                print(f'transformed Input: {Input}')

                cv.circle(r_img, (x,y), 3, [0, 0, 255], -1)
                cv.putText(r_img, f"IMG CORDS: x:{x} - y:{y} - depth:{proc_d_img[y,x]}", (0, 60), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                prediction = model.predict(Input[:,:])
                print(f'raw Prediction: {prediction}')
                prediction = scalerY.inverse_transform(prediction)
                
                prediction = np.round(prediction, 2)
                print(f'transformed prediction : {prediction}')
                if prediction.shape[1] == 2:
                    cv.putText(r_img, f"PREDICTION: x:{prediction[0, 0]} - y:{prediction[0, 1]} - z: /", (0, 30), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                else:
                    cv.putText(r_img, f"PREDICTION: x:{prediction[0, 0]} - y:{prediction[0, 1]} - z: {prediction[0, 2]}", (0, 30), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

                ORIENTATION = np.array([0,-3.143, 0]) #Standard Orientation for Grasping
                #ORIENTATION = np.array([0, 2.220, -2.220]) #Standard Orientation for Grasping

                if State == 0:
                    print('#GRASPING PIECE#')
                    x_offset = 0
                    y_offset = 0
                    print('Opening Gripper...')
                    Robot.ActuateGripper(40)
                    
                    print(f'Driving to chosen position with z offset 150 and applying x: {x_offset}mm and y: {y_offset}mm offset...')
                    Pose_offset = np.array([prediction[0, 0]+x_offset, prediction[0, 1]+y_offset, 150, ORIENTATION[0], ORIENTATION[1], ORIENTATION[2]])
                    Robot.MoveC(Pose_offset)

                    print('Driving to grasp area...')
                    Pose = np.array([prediction[0, 0]+x_offset, prediction[0, 1]+y_offset, 58, ORIENTATION[0], ORIENTATION[1], ORIENTATION[2]])
                    Robot.MoveC(Pose, 0.2, 0.1)

                    print('Grasping Chess piece...')
                    Robot.CloseGripper()

                    tempstat, temppos = Robot.CheckGripperStatus()
                    print(f'Gripper Status: {tempstat}, Gripper Position: {temppos}')
                    if tempstat.value == 2:
                        State = 1
                        print('Chess Piece successfully grasped!')
                        print('Next selection will determine the placing position.')
                    else:
                        State = 0
                        print('No Chess Piece grasped...')
                        print('Next selection will be another grasping attempt.')
                    if s==1:
                        print('SLIDING_MODE! Will slide piece to target position')
                    
                    else:
                        print('Moving Home...')
                        Pose = Robot.WhereC()
                        Pose[2] = Pose[2]+100
                        Robot.MoveC(Pose)
                        Robot.Home() 
                    print('finished! you may choose a new point now.')
                else:
                    print('#PLACING PIECE#')
                    x_offset = 0 #-20
                    y_offset = 0 #5
                    print(s)
                    if s==1:
                        print('sliding piece to taget with applying x: {x_offset}mm and y: {y_offset}mm offset...')
                        Pose_offset = np.array([prediction[0, 0]+x_offset, prediction[0, 1]+y_offset, 59, ORIENTATION[0], ORIENTATION[1], ORIENTATION[2]])
                        Robot.MoveC(Pose_offset)
                    else:
                        print(f'Driving to chosen position with z offset 150 and applying x: {x_offset}mm and y: {y_offset}mm offset...')
                        Pose_offset = np.array([prediction[0, 0]+x_offset, prediction[0, 1]+y_offset, 150, ORIENTATION[0], ORIENTATION[1], ORIENTATION[2]])
                        Robot.MoveC(Pose_offset)
                        
                        print('Driving to placing area...')
                        Pose = np.array([prediction[0, 0]+x_offset, prediction[0, 1]+y_offset, 58, ORIENTATION[0], ORIENTATION[1], ORIENTATION[2]])
                        Robot.MoveC(Pose, 0.2, 0.1)

                    print('Placing Piece...')
                    Robot.ActuateGripper(30)

                    print('Piece placed.')
                    print('Next selection will be a new grasping attempt.')
                    print('Moving Home...')
                    Pose = Robot.WhereC()
                    Pose[2] = Pose[2]+100
                    Robot.MoveC(Pose)
                    Robot.Home()
                    State = 0
                    print('finished! you may choose a new point now.')
def main():
    global c_img, proc_d_img, model, Robot, r_img
    Robot = UR10Robot()
    TRAINING_HOME_Init = np.array([0, -120, 120, 0, -90, -180]) #has to be called because the robot will otherwise crash into the camera
    TRAINING_HOME = np.array([60, -120, 120, 0, 90, 180])
    #Robot.MoveJ(TRAINING_HOME_Init)
    #Robot.MoveJ(TRAINING_HOME)
    #NAME = "CUSTOM_NN_3x64x128x64x3_nData2969_nEpochs1000_mae_Norm_1_FH_False_Input3_Output2_loss_mae_batch_50_Optimizer_adam" #DAS MIT HÖHEREM SCHACHFELD!!! DAS KLAPPT ECHT GUT!
    NAME = "CUSTOM_NN_3x8x16x8x3_nData4119_nEpochs1000_mae_Norm_1_FH_False_Input3_Output2_loss_mae_batch_50_Optimizer_adam_OldData" #Abweichungen im oberen Schachfeldbereich
    model = keras.models.load_model("C:/ChessterNNModels/"+NAME)
    Camera = RealSenseCamera() 
    time.sleep(1) 
    switch = 'Sliding:'
    cv.namedWindow("Img",1)
    cv.setMouseCallback("Img", onmouseT)
    cv.createTrackbar(switch, 'Img',0,1,nothing)
    c_img = Camera.capture_color()
    dimg, dframe = Camera.capture_depth()
    time.sleep(1)

    while True:
        c_img = Camera.capture_color()
        dimg, dframe = Camera.capture_depth()
        proc_d_img = Camera.fill_holes(dframe)
        stack = np.hstack((c_img, r_img))
        cv.imshow("Img", stack)
        cv.waitKey(33)
    
if __name__ == "__main__":
    main()