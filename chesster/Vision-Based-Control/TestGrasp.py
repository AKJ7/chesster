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
from sklearn.preprocessing import MinMaxScaler, StandardScaler
Robot = None
model = None
c_img=[]
d_img=[]
State=0

def lin_reg_result(X, Y, coeff = np.array([1.06015269e+03, -5.94343938e-01, -1.89386788e-01])):
    Z = coeff[1]*X+coeff[2]*Y+coeff[0]
    return Z

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

def onmouse(event, x, y, flags, param):
    global c_img, d_img, model, Robot, State
    if event == cv.EVENT_LBUTTONDOWN:
        Input = np.array([x, y, d_img[y,x]]) #Flipped!
        Input = Input.astype(float)  
        Input = Input[np.newaxis, :]

        print(f'raw Input: {Input}')
        _, _, _, _, scalerX, scalerY = get_Data(3, 3, Norm=1, Fixed_height=False, XName="Input594Filtered.csv", YName="Output594Filtered.csv")
        Input = scalerX.transform(Input)
        print(f'transformed Input: {Input}')

        cv.circle(c_img, (x,y), 3, [0, 0, 255], -1)
        cv.putText(c_img, f"IMG CORDS: x:{x} - y:{y} - depth:{d_img[y,x]}", (x-40, y-20), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        prediction = model.predict(Input[:,:])
        print(f'raw Prediction: {prediction}')
        prediction = scalerY.inverse_transform(prediction)
        
        prediction = np.round(prediction, 2)
        print(f'transformed prediction : {prediction}')

        cv.putText(c_img, f"PREDICTION: x:{prediction[0, 0]} - y:{prediction[0, 1]} - z: {prediction[0, 2]}", (x-40, y-60), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        cv.imshow("Img", c_img)

        ORIENTATION = np.array([0,-3.143, 0]) #Standard Orientation for Grasping
        #ORIENTATION = np.array([0, 2.220, -2.220]) #Standard Orientation for Grasping

        if State == 0:
            print('#GRASPING PIECE#')
            
            print('Opening Gripper...')
            Robot.ActuateGripper(50)

            print('Driving to chosen position with offset 150...')
            Pose_offset = np.array([prediction[0, 0], prediction[0, 1], 150, ORIENTATION[0], ORIENTATION[1], ORIENTATION[2]])
            Robot.MoveC(Pose_offset)

            print('Driving to grasp area...')
            Pose = np.array([prediction[0, 0], prediction[0, 1], 50, ORIENTATION[0], ORIENTATION[1], ORIENTATION[2]])
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
            print('Moving Home...')
            Pose = Robot.WhereC()
            Pose[2] = Pose[2]+100
            Robot.MoveC(Pose)
            Robot.Home() 
        else:
            print('#PLACING PIECE#')
            
            print('Driving to chosen position with offset 100...')
            Pose_offset = np.array([prediction[0, 0], prediction[0, 1], 150, ORIENTATION[0], ORIENTATION[1], ORIENTATION[2]])
            Robot.MoveC(Pose_offset)
            
            print('Driving to placing area...')
            Pose = np.array([prediction[0, 0], prediction[0, 1], 50, ORIENTATION[0], ORIENTATION[1], ORIENTATION[2]])
            Robot.MoveC(Pose, 0.2, 0.1)

            print('Placing Piece...')
            Robot.ActuateGripper(50)

            print('Piece placed.')
            print('Next selection will be a new grasping attempt.')
            print('Moving Home...')
            Pose = Robot.WhereC()
            Pose[2] = Pose[2]+100
            Robot.MoveC(Pose)
            Robot.Home()
            State = 0
def main():
    global c_img, d_img, model, Robot
    Robot = UR10Robot()
    TRAINING_HOME_Init = np.array([0, -120, 120, 0, -90, -180]) #has to be called because the robot will otherwise crash into the camera
    TRAINING_HOME = np.array([60, -120, 120, 0, 90, 180])
    #Robot.MoveJ(TRAINING_HOME_Init)
    #Robot.MoveJ(TRAINING_HOME)
    NAME = "nD0_nN20_DpOut0_nData2969_nEpochs1500_mae_Norm_1_FH_False_Input3_Output3_loss_mae_batch_50NEW DATA_TILTED_TCP_TEST" #Dieses hier performt RICHTIG Gut bei Aufnehmen,
    NAME = "nD0_nN20_DpOut0_nData496_nEpochs1500_mae_Norm_1_FH_False_Input3_Output3_loss_mae_batch_50NEW DATA_TILTED_TCP"#Das beim Absetzen -> das erste dafür dabei SEHR schlecht?!?!?
    model = keras.models.load_model("C:/Chesster NN Models/"+NAME)
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