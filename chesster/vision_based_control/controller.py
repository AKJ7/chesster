from pathlib import Path
import os
from shutil import ReadError
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
        logger.info('Constructing VB-Controller...')
        self.__model_path = model_path
        logger.info(f'Reading Neural Network from path: {self.__model_path}')
        self.__model_name = "NN2"
        logger.info(f'Using Neural Network Model: {self.__model_name}')
        self.__scaler_path = scaler_path
        logger.info(f'Reading scaler from path: {self.__scaler_path}')
        self.__robot = robot
        logger.info('Setting Class intern variables...')
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
        self.__conversionQueenPosition = [np.array([-258.60, -640.7]), np.array([-260.6, -587.6]), np.array([-263.88, -537.11])]
        self.__conversionKnightPosition = []
        self.__wasteBinPosition = np.array([-195.15, -333.82])
        self.__currentAvailableQueens = 3 #Number of Queens placed on a fixed position for conversion
        self.__currentAvailableKnights = 0 #Number of Knights placed on a fixed position for conversion
        self.__intermediateOrientation = np.array([0, 0, -1.742])
        logger.info(f'Number of Queens for promotion available: {self.__currentAvailableQueens}')
        logger.info(f'Number of Knights for promotion available: {self.__currentAvailableKnights}')

    def start(self):
        cwd = os.getcwd()
        path = cwd+'\\'+self.__model_path+self.__model_name
        try:
            logger.info('Trying to read in Neural Network...')
            self.__neural_network = keras.models.load_model(path)
        except Exception:
            logger.info('Reading failed. No matching Directory/Model found.')
            raise Exception
        else:
            logger.info('Reading Neural Network successful.')
        try:
            logger.info('Trying to read in Neural Network...')    
            self.getScaler("ScalerDataX.csv","ScalerDataY.csv")
        except Exception:
            logger.info('Reading Scaler Data failed. No matching Directory or Files found')
            raise Exception
        else:
            logger.info('Reading Scaler Data successful.')

    def stop(self):
        pass

    def getScaler(self, xName: str, yName: str):
        """
        imports scalers for the normalized data. Is based on the Trainingdata on which the neural network is trained.
        """
        cwd = os.getcwd()
        path = cwd+'\\'+self.__scaler_path
        X = ImportCSV(path, xName, ";")
        X = np.round(X, 3)
        Y = ImportCSV(path, yName, ";")
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
            logger.info('Processing Capture Move...')
            self.__graspArray = np.array([ChessPiece[0].y_cimg, ChessPiece[0].x_cimg, ChessPiece[0].zenith])
            self.__placeArray = self.__wasteBinPosition
            logger.info(f'Grasp Array (px coords): {self.__graspArray}')
            logger.info(f'Place Array (world coords): {self.__placeArray}')
            self.__heights[0] = 69
            self.__heights[1] = 130
            logger.info(f'setting heights for future z-coords to: {self.__heights}')
            self.__flag = 'capture'
        elif 'P' in self.__currentMove:
            logger.info('Processing Promotion Move...')
            if ('PQ' in self.__currentMove) or ('Pq' in self.__currentMove):                   #Case: Conversion to Queen
                self.__graspArray = self.__conversionQueenPosition.pop(-1)
                logger.info(f'Grasp Array for queen promotion move: {self.__graspArray}')
            else:                                           #Case: Conversion to Knight
                self.__graspArray = self.__conversionKnightPosition.pop(-1)
                logger.info(f'Grasp Array for knight promotion move: {self.__placeArray}')
            x = int(np.round(ChessPiece[1].roi[0]*ScalingFactors[0], 0))
            y = int(np.round(ChessPiece[1].roi[1]*ScalingFactors[1], 0))
            logger.info(f'Scaling ROI of target chess field from x: {ChessPiece[1].roi[0]}, y: {ChessPiece[1].roi[1]} to x_scaled: {x}, y_scaled: {y}')
            self.__placeArray = np.array([x, y, d_img[y,x]])
            logger.info(f'Place Array: {self.__placeArray}')
            self.__flag = 'promotion'
            self.__heights[0] = 50 #tbd aber tiefer als regular, weil neben dem Feld
            self.__heights[1] = 68
            logger.info(f'Setting heights for future z-coords to: {self.__heights}')
        else:
            logger.info('Processing Regular Move...')
            x = int(np.round(ChessPiece[1].roi[0]*ScalingFactors[0], 0))
            y = int(np.round(ChessPiece[1].roi[1]*ScalingFactors[1], 0))
            logger.info(f'Scaling ROI of target chess field from x: {ChessPiece[1].roi[0]}, y: {ChessPiece[1].roi[1]} to x_scaled: {x}, y_scaled: {y}')
            self.__graspArray = np.array([ChessPiece[0].y_cimg, ChessPiece[0].x_cimg, ChessPiece[0].zenith])
            logger.info(f'Grasp Array: {self.__graspArray}')
            self.__placeArray = np.array([x, y, d_img[y,x]]) #TBD!
            logger.info(f'Place Array: {self.__placeArray}')
            self.__heights[0] = 69 #height for grasping piece
            self.__heights[1] = 69 #height for placing piece
            logger.info(f'Setting heights for future z-coords to: {self.__heights}')
            self.__flag = 'normal'

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
            logger.info('Processing Arrays for capture move...')
            graspInput = self.__scalerX.transform(graspInput)
            logger.info('normalizing Grasp Array to [-1, 1]')
            #Add empty axis. Necessary for Keras Prediction of shape (1,3)
            logger.info('predicting Output for Grasp Array with NN...')
            graspOutput = self.__neural_network.predict(graspInput)
            logger.info('Retransform Output...')
            self.__graspAction = self.__scalerY.inverse_transform(graspOutput)
            self.__placeAction = self.__placeArray #just copy Pose from processMove
        elif self.__flag == 'promotion':                                #case: Promotion
            logger.info('Processing Arrays for promotion move...')
            logger.info('normalizing Place Array to [-1, 1]')
            placeInput = self.__scalerX.transform(placeInput)
            #Add empty axis. Necessary for Keras Prediction of shape (1,3)
            logger.info('predicting Output for Place Array with NN...')
            placeOutput = self.__neural_network.predict(placeInput)
            logger.info('Retransform Output...')
            self.__placeAction = self.__scalerY.inverse_transform(placeOutput)
            self.__graspAction = self.__graspArray #just copy Pose from processMove
        else:                                                           #case: normal move
            logger.info('Processing Arrays for regular move...')
            logger.info('normalizing Grasp Array to [-1, 1]')
            graspInput = self.__scalerX.transform(graspInput) #normalize raw data according to training data of NN
            logger.info('normalizing Place Array to [-1, 1]')
            placeInput = self.__scalerX.transform(placeInput)
            logger.info('predicting Output for Grasp Array with NN...')
            graspOutput = self.__neural_network.predict(graspInput) #predict TCP-Coordinates in normalized format
            logger.info('predicting Output for Place Array with NN...')
            placeOutput = self.__neural_network.predict(placeInput)
            logger.info('Retransform Outputs...')
            self.__graspAction = self.__scalerY.inverse_transform(graspOutput) #convert normalized data to mm 
            self.__placeAction = self.__scalerY.inverse_transform(placeOutput)
        logger.info(f'Grasp Array in world coords for robot: {self.__graspAction}')
        logger.info(f'Place Array in world coords for robot: {self.__placeAction}')

    def makeMove(self):
        """
        Processes the obtained action arrays for grasp and place. Fixed orientations and heights are assigned and then send to the
        Robot Class method MoveChesspiece.
        """
        logger.info(f'preparing trajectory for robot')
        graspPose = np.zeros(6)
        graspPose[0:2] = self.__graspAction
        graspPose[0] = graspPose[0]
        graspPose[1] = graspPose[1]
        graspPose[2] = self.__heights[0]
        graspPose[3:] = self.__ORIENTATION
        
        placePose = np.zeros(6)
        placePose[0:2] = self.__placeAction
        placePose[0] = placePose[0]#+5
        placePose[1] = placePose[1]+3
        placePose[2] = self.__heights[1]
        placePose[3:] = self.__ORIENTATION

        logger.info(f'Final grasp pose: {graspPose}')
        logger.info(f'Final place pose: {placePose}')

        logger.info('Moving Chesspiece.')
        self.__robot.MoveChesspiece(graspPose, placePose, self.__intermediateOrientation, 100)

    def useVBC(self, Move: str, Pieces: list, d_img: np.ndarray, ScalingFactors: list, lastMove: bool):
        """
        Main method of the Vision Based Controller. This method is the only one that should be called by the user. 
        Executes all neccessary methods for a movement of a piece.
        """
        self.__currentMove = Move
        logger.info(f'VBC processing move: {self.__currentMove}')
        self.processMove(Pieces, d_img, ScalingFactors)
        self.processActions()
        self.makeMove()
        if lastMove == True:
            logger.info('Last move of moveset. Proceeding to drive home... ')
            self.__robot.Home()
