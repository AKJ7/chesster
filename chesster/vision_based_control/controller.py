from pathlib import Path
import os
from typing import Union
from chesster.master.action import Action
from chesster.master.module import Module
from chesster.Robot.UR10 import UR10Robot
import keras
import logging
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from chesster.moduls.GenericSysFunctions import ImportCSV
logger = logging.getLogger(__name__)

class VisualBasedController(Module):
    def __init__(self, robot: UR10Robot, model_path: Union[str, os.PathLike], scaler_path: str):
        self.__model_path = model_path
        self.__model_name = "NeuralNetwork3x64x128x64x2"
        self.__scaler_path = scaler_path
        self.__robot = robot
        self.__ORIENTATION = np.array([0,-3.143, 0])
        self.__graspArray = np.zeros(3)
        self.__placeArray = np.zeros(3)
        self.__graspAction = np.zeros(0)
        self.__placeAction = np.zeros(3)
        self.__heights = np.zeros(2)
        self.__flag = "None"
        self.__scalerY = None
        self.__scalerX = None
        self.__currentMove = "None"
        self.__ALPHABET = 'abcdefgh'
        self.__conversionQueenPosition = [np.array([-263.29, -585.30]), np.array([-263.30, -637.03])]
        self.__conversionKnightPosition = [np.array([-263.88, -537.11])]
        self.__wasteBinPosition = np.array([-195.15, -333.82])
        self.__currentAvailableQueens = 2 #Number of Queens placed on a fixed position for conversion
        self.__currentAvailableKnights = 1 #Number of Knights placed on a fixed position for conversion
        self.__intermediateOrientation = np.array([0, 0, -1.742])


    def start(self):
        self.__neural_network = keras.models.load_model(self.__model_path+self.__model_name)
        self.getScaler("ScalerDataX.csv","ScalerDataY.csv")

    def stop(self):
        pass

    def run(self, action: Action):
        pass
    
    def getScaler(self, xName: str, yName: str):
        """
        imports scalers for the normalized data. Is based on the Trainingdata on which the neural network is trained.
        """
        Dir = self.__scaler_path
        X = ImportCSV(Dir, xName, ";")
        X = np.round(X, 3)
        Y = ImportCSV(Dir, yName, ";")
        Y = np.round(Y, 3)
        X = np.transpose(X)
        Y = np.transpose(Y)
        self.__scalerX = MinMaxScaler(feature_range=(-1,1))
        self.__scalerX.fit(X[:, :])
        self.__scalerY = MinMaxScaler(feature_range=(-1,1))
        self.__scalerY.fit(Y[:, 0:2])

    def processMove(self, ChessPiece, d_img, ScalingFactors):
        """
        Method used for processing the Move Command. Based on a prefix (xx, PQ, no prefix) a specified action is performed:
        x: capture move -> xxe3
        PQ/PN: Promotion to Queen or Knight
        None: Regular Move from field x to field y
        """
        if 'x' in self.__currentMove: #Capture move
            self.__graspArray = np.array([ChessPiece[0].y_cimg, ChessPiece[0].x_cimg, ChessPiece[0].zenith])
            self.__placeArray = self.__wasteBinPosition
            self.__heights[0] = 58
            self.__heights[1] = 130
            self.__flag = 'capture'
            print(f'GraspArray [px,px,mm]: {self.__graspArray}')
            print(f'PlaceArray [mm,mm]: {self.__placeArray}')
        elif 'P' in self.__currentMove:
            MoveExtraced = self.__currentMove[-2:] #example format for promotion string : PQe1
            if 'PQ' in self.__currentMove:                   #Case: Conversion to Queen
                self.__graspArray = self.__conversionQueenPosition.pop(-1)
            else:                                           #Case: Conversion to Knight
                self.__graspArray = self.__conversionKnightPosition.pop(-1)
            x = int(np.round(ChessPiece[1].roi[0]*ScalingFactors[0], 0))
            y = int(np.round(ChessPiece[1].roi[1]*ScalingFactors[1], 0))
            self.__placeArray = np.array([x, y, d_img[y,x]]) #TBD!
            self.__flag = 'promotion'
            self.__heights[0] = 45 #tbd aber tiefer als regular, weil neben dem Feld
            self.__heights[1] = 58
            print(f'GraspArray [mm,mm]: {self.__graspArray}')
            print(f'PlaceArray [px,px,mm]: {self.__placeArray}')
        else:
            MoveExtraced = self.__currentMove #example format for regular move: e2e4
            x = int(np.round(ChessPiece[1].roi[0]*ScalingFactors[0], 0))
            y = int(np.round(ChessPiece[1].roi[1]*ScalingFactors[1], 0))
            self.__graspArray = np.array([ChessPiece[0].y_cimg, ChessPiece[0].x_cimg, ChessPiece[0].zenith])
            self.__placeArray = np.array([x, y, d_img[y,x]]) #TBD!
            self.__heights[0] = 58 #height for grasping piece
            self.__heights[1] = 58 #height for placing piece
            self.__flag = 'normal'
            print(f'GraspArray [px,px,mm]: {self.__graspArray}')
            print(f'PlaceArray [px,px,mm]: {self.__placeArray}')

    def processActions(self):
        """
        Method used for defining the pose arrays which are send to the robot. Arrays are based on the flag (move categorie x / QQ / None).
        - for capture (x) only the grasp pose is predicted by the neural network
        - for promotion (QQ/QK) only the place pose is predicted by the neural network
        - for a regular move (None) grasp as well as place poses are predicted by the neural network 
        """
        graspInput = self.__graspArray
        graspInput = graspInput[np.newaxis, :]
        placeInput = self.__placeArray
        placeInput = placeInput[np.newaxis, : ]
        if self.__flag == 'capture':                                    #case: capture
            graspInput = self.__scalerX.transform(graspInput)
            #Add empty axis. Necessary for Keras Prediction of shape (1,3)
            graspOutput = self.__neural_network.predict(graspInput)
            self.__graspAction = self.__scalerY.inverse_transform(graspOutput)
            self.__placeAction = self.__placeArray #just copy Pose from processMove
        elif self.__flag == 'promotion':                                #case: Promotion
            placeInput = self.__scalerX.transform(placeInput)
            #Add empty axis. Necessary for Keras Prediction of shape (1,3)
            placeOutput = self.__neural_network.predict(placeInput)
            self.__placeAction = self.__scalerY.inverse_transform(placeOutput)
            self.__graspAction = self.__graspArray #just copy Pose from processMove
        else:                                                           #case: normal move
            graspInput = self.__scalerX.transform(graspInput) #normalize raw data according to training data of NN
            placeInput = self.__scalerX.transform(placeInput)

            graspOutput = self.__neural_network.predict(graspInput) #predict TCP-Coordinates in normalized format
            placeOutput = self.__neural_network.predict(placeInput)

            self.__graspAction = self.__scalerY.inverse_transform(graspOutput) #convert normalized data to mm 
            self.__placeAction = self.__scalerY.inverse_transform(placeOutput)

    def makeMove(self):
        """
        Processes the obtained action arrays for grasp and place. Fixed orientations and heights are assigned and then send to the
        Robot Class method MoveChesspiece.
        """
        graspPose = np.zeros(6)
        graspPose[0:2] = self.__graspAction
        graspPose[2] = self.__heights[0]
        graspPose[3:] = self.__ORIENTATION

        placePose = np.zeros(6)
        placePose[0:2] = self.__placeAction
        placePose[2] = self.__heights[1]
        placePose[3:] = self.__ORIENTATION

        self.__robot.MoveChesspiece(graspPose, placePose, self.__intermediateOrientation, 100)
        #self.__robot.Home()

    def useVBC(self, Move: str, Pieces: list, d_img: np.ndarray, ScalingFactors: list, lastMove: bool):
        """
        Main method of the Vision Based Controller. This method is the only one that should be called by the user. 
        Executes all neccessary methods for a movement of a piece.
        """
        self.__currentMove = Move
        self.processMove(Pieces, d_img, ScalingFactors)
        self.processActions()
        self.makeMove()
        if lastMove == True:
            self.__robot.Home()
