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
        self.__graspArray = np.zeros(3)
        self.__placeArray = np.zeros(3)
        self.__heights = np.zeros(2)
        self.__flag = "None"
        self.__scalerY = None
        self.__scalerX = None

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

    def processMove(self, Move: str, ChessPieces):
        ALPHABET = 'abcdefgh'
        MoveExtraced = Move[-4:]
        if 'x' in Move: #Capture move
            GraspIndices = [ALPHABET.find(MoveExtraced[0]), int(MoveExtraced[1])] #Row, Col in ChessPiece Matrix
            self.__graspArray = np.array([ChessPiece[GraspIndices[0], GraspIndices[1]].x,
                                ChessPiece[GraspIndices[0], GraspIndices[1]].y,
                                ChessPiece[GraspIndices[0], GraspIndices[1]].depth])
            self.__placeArray = np.array(POSEXYZ) #Enter Pose for "waste bag" ODER FARBKODIERUNG?!
            self.__heights[0] = 58
            self.__heights[1] = 120 
            self.__flag = 'capture'
        elif 'QQ' in Move:
            pass #Hier Ablauf für Bauernumwandlung
            self.__flag = 'conversion'
        else:
            GraspIndices = [ALPHABET.find(MoveExtraced[0]), int(MoveExtraced[1])] #Row, Col in ChessPiece Matrix
            PlaceIndices = [ALPHABET.find(MoveExtraced[2]), int(MoveExtraced[3])] #Row, Col in ChessPiece Matrix
            self.__graspArray = np.array([ChessPiece[GraspIndices[0], GraspIndices[1]].x,
                                ChessPiece[GraspIndices[0], GraspIndices[1]].y,
                                ChessPiece[GraspIndices[0], GraspIndices[1]].depth])
            self.__placeArray = np.array([ChessPiece[PlaceIndices[0], PlaceIndices[1]].x,
                                ChessPiece[PlaceIndices[0], PlaceIndices[1]].y,
                                ChessPiece[PlaceIndices[0], PlaceIndices[1]].depth])
            self.__heights[0] = 58 #height for grasping piece
            self.__heights[1] = 58 #height for placing piece
            self.__flag = 'normal'

    def processInput(self, Input):
        Input = Input[np.newaxis, :] #Add empty axis. Necessary for Keras Prediction of shape (1,3)
        if self.__flag == 'capture':
            Output = Input
        else:
            Input = self.__scalerX.transform(Input) #transform Input from mm to normalized [-1,1]
            Output = self.__neural_network.predict(Input)
            Output = self.__scalerY.inverse_transform(Output) #transform Output from normalized [-1,1] to mm 
        return Output[0,:]