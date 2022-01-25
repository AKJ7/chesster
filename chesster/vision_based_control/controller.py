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
    def __init__(self, robot: UR10Robot, model_path: Union[str, os.PathLike]):
        self.__model_path = model_path
        self.__model_name = ""
        self.__robot = robot
        self.__ORIENTATION = np.array([0,-3.143, 0])
        self.__graspArray = np.zeros(3)
        self.__placeArray = np.zeros(3)
        self.__graspAction = np.zeros(3)
        self.__placeAction = np.zeros(3)
        self.__heights = np.zeros(2)
        self.__flag = "None"
        self.__scalerY = None
        self.__scalerX = None
        self.__current_move = "None"
        self.__ALPHABET = 'abcdefgh'
        self.__conversionQueenPosition = [np.array([POS1]), np.array([POS2])]
        self.__conversionKnightPosition = [np.array([POS1])]
        self.__wasteBinPosition = np.array([POSEXYZ])
        self.__currentAvailableQueens = 2 #Number of Queens placed on a fixed position for conversion
        self.__currentAvailableKnights = 1 #Number of Knights placed on a fixed position for conversion

    def start(self):
        self.__neural_network = keras.models.load_model("C:/Users/admin/Desktop/ML/ChessterModels/"+self.__model_name)
        self.getScaler("","")

    def stop(self):
        pass

    def run(self, action: Action):
        pass
    
    def getScaler(self, xName: str, yName: str):
        DIRPATH = os.path.dirname(__file__)
        Dir = DIRPATH+"/Trainingsdaten/"
        X = ImportCSV(Dir, xName, ";")
        X = np.round(X, 3)
        Y = ImportCSV(Dir, yName, ";")
        Y = np.round(Y, 3)
        X = np.transpose(X)
        Y = np.transpose(Y)
        self.__scalerX = MinMaxScaler(feature_range=(-1,1))
        self.__scalerX.fit(X[:, :])
        self.__scalerY = MinMaxScaler(feature_range=(-1,1))
        self.__scalerY.fit(Y[:, :])

    def processMove(self, ChessPiece):
        
        if 'x' in self.__current_move: #Capture move
            MoveExtraced = self.__current_move[-2:] #example format for capture: xe4
            GraspIndices = [self.__ALPHABETBET.find(MoveExtraced[0]), int(MoveExtraced[1])] #Row, Col in ChessPiece Matrix
            self.__graspArray = np.array([ChessPiece[GraspIndices[0], GraspIndices[1]].x,
                                ChessPiece[GraspIndices[0], GraspIndices[1]].y,
                                ChessPiece[GraspIndices[0], GraspIndices[1]].depth])
            self.__placeArray = self.__wasteBinPosition
            self.__heights[0] = 58
            self.__heights[1] = 120 
            self.__flag = 'capture'
        elif 'Q' in self.__current_move:
            MoveExtraced = self.__current_move[-2:] #example format for promotion string : QQe1
            if 'QQ' in self.__current_move:                   #Case: Conversion to Queen
                self.__graspArray = self.__conversionQueenPosition.pop(-1)
            else:                                           #Case: Conversion to Knight
                self.__graspArray = self.__conversionKnightPosition.pop(-1)
            PlaceIndices = [self.__ALPHABET.find(MoveExtraced[2]), int(MoveExtraced[3])] #Row, Col in ChessPiece Matrix
            self.__placeArray = np.array([ChessPiece[PlaceIndices[0], PlaceIndices[1]].x,
                                ChessPiece[PlaceIndices[0], PlaceIndices[1]].y,
                                ChessPiece[PlaceIndices[0], PlaceIndices[1]].depth])
            self.__flag = 'promotion'
            self.__heights[0] = 45 #tbd aber tiefer als regular, weil neben dem Feld
            self.__heights[1] = 58
        else:
            MoveExtraced = self.__current_move #example format for regular move: e2e4
            GraspIndices = [self.__ALPHABET.find(MoveExtraced[0]), int(MoveExtraced[1])] #Row, Col in ChessPiece Matrix
            PlaceIndices = [self.__ALPHABET.find(MoveExtraced[2]), int(MoveExtraced[3])] #Row, Col in ChessPiece Matrix
            self.__graspArray = np.array([ChessPiece[GraspIndices[0], GraspIndices[1]].x,
                                ChessPiece[GraspIndices[0], GraspIndices[1]].y,
                                ChessPiece[GraspIndices[0], GraspIndices[1]].depth])
            self.__placeArray = np.array([ChessPiece[PlaceIndices[0], PlaceIndices[1]].x,
                                ChessPiece[PlaceIndices[0], PlaceIndices[1]].y,
                                ChessPiece[PlaceIndices[0], PlaceIndices[1]].depth])
            self.__heights[0] = 58 #height for grasping piece
            self.__heights[1] = 58 #height for placing piece
            self.__flag = 'normal'

    def processActions(self):
        graspInput = self.__graspArray[np.newaxis, :]#Add empty axis. Necessary for Keras Prediction of shape (1,3)
        placeInput = self.__placeArray[np.newaxis, :]#Add empty axis. Necessary for Keras Prediction of shape (1,3)
        if self.__flag == 'capture':                                    #case: capture
            graspInput = self.__scalerX.transform(graspInput)
            graspOutput = self.__neural_network.predict(graspInput)
            self.__graspAction = self.__scalerY.inverse_transform(graspOutput)

            self.__placeAction = self.__placeArray #just copy Pose from processMove
        elif self.__flag == 'promotion':                                #case: Promotion
            placeInput = self.__scalerX.transform(placeInput)
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
            PoseGrasp = np.zeros(6)
            PoseGrasp[0:2] = self.__graspAction
            PoseGrasp[2] = self.__heights[0]+100
            PoseGrasp[3:] = self.__ORIENTATION

            PosePlace = np.zeros(6)
            PosePlace[0:2] = self.__placeAction
            PosePlace[2] = self.__heights[1]+100
            PosePlace[3:] = self.__ORIENTATION
            #####
            #Grasp
            #####
            self.__robot.MoveC(PoseGrasp)
            PoseGrasp[2] = PoseGrasp[2]-100
            self.__robot.MoveC(PoseGrasp)
            self.__robot.CloseGripper()
            PoseGrasp[2] = PoseGrasp[2]+100
            self.__robot.MoveC(PoseGrasp)
            #####
            #Place
            #####
            self.__robot.MoveC(PosePlace)
            PosePlace[2] = PosePlace[2]-100
            self.__robot.MoveC(PosePlace)
            self.__robot.ActuateGripper(30)
            PosePlace[2] = PosePlace[2]+100
            self.__robot.MoveC(PosePlace)

            self.__robot.Home()

    def useVBC(self, Move: str, ChessPieces):
        self.processMove(ChessPieces)
        self.processActions()
        self.makeMove()
