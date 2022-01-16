import sys as sys
import os as os

from numpy.lib.function_base import place
sys.path.append(os.path.dirname(sys.path[0])) #preperation for import of custom moduls
from moduls.ImageProcessing import ExtractImageCoordinates, FigureMapping
import tensorflow as tf
import keras as keras
import numpy as np
import cv2 as cv

def ProcessMove(Move: str, ChessPieces):
    ALPHABET = 'abcdefgh'
    MoveExtraced = Move[-4:]
    graspArray = np.zeros(3)
    placeArray = np.zeros(3)
    heights = np.zeros(2)
    if 'x' in Move: #Capture move
        GraspIndices = [ALPHABET.find(MoveExtraced[0]), int(MoveExtraced[1])] #Row, Col in ChessPiece Matrix
        graspArray = np.array([ChessPiece[GraspIndices[0], GraspIndices[1]].x,
                              ChessPiece[GraspIndices[0], GraspIndices[1]].y,
                              ChessPiece[GraspIndices[0], GraspIndices[1]].depth])
        placeArray = np.array(POSEXYZ) #Enter Pose for "waste bag" ODER FARBKODIERUNG?!
        heights[0] = 58
        heights[1] = 120 
        flag = 'capture'
    elif 'QQ' in Move:
        pass #Hier Ablauf für Bauernumwandlung
        flag = 'conversion'
    else:
        GraspIndices = [ALPHABET.find(MoveExtraced[0]), int(MoveExtraced[1])] #Row, Col in ChessPiece Matrix
        PlaceIndices = [ALPHABET.find(MoveExtraced[2]), int(MoveExtraced[3])] #Row, Col in ChessPiece Matrix
        graspArray = np.array([ChessPiece[GraspIndices[0], GraspIndices[1]].x,
                              ChessPiece[GraspIndices[0], GraspIndices[1]].y,
                              ChessPiece[GraspIndices[0], GraspIndices[1]].depth])
        placeArray = np.array([ChessPiece[PlaceIndices[0], PlaceIndices[1]].x,
                              ChessPiece[PlaceIndices[0], PlaceIndices[1]].y,
                              ChessPiece[PlaceIndices[0], PlaceIndices[1]].depth])
        heights[0] = 58 #height for grasping piece
        heights[1] = 58 #height for placing piece
        flag = 'normal'
        
    return graspArray, placeArray, heights, flag

def ProcessInput(NeuralNetworkModel, Input, ScalerX, ScalerY, flag):
    Input = Input[np.newaxis, :] #Add empty axis. Necessary for Keras Prediction of shape (1,3)
    if flag == 'capture':
        Output = Input
    else:
        Input = ScalerX.transform(Input) #transform Input from mm to normalized [-1,1]
        Output = NeuralNetworkModel.predict(Input)
        Output = ScalerY.inverse_transform(Output) #transform Output from normalized [-1,1] to mm 
    return Output[0,:]

def MakeMove(Robot, GraspArray, PlaceArray, ORIENTATION, Heights): #currently only implemented simple grasp and place of a piece
    PoseGrasp = np.zeros(6)
    PoseGrasp[0:2] = GraspArray
    PoseGrasp[2] = Heights[0]+100
    PoseGrasp[3:] = ORIENTATION

    PosePlace = np.zeros(6)
    PosePlace[0:2] = PlaceArray
    PosePlace[2] = Heights[1]+100
    PosePlace[3:] = ORIENTATION

    Robot.MoveC(PoseGrasp)
    PoseGrasp[2] = PoseGrasp[2]-100
    Robot.MoveC(PoseGrasp)
    Robot.CloseGripper()
    PoseGrasp[2] = PoseGrasp[2]+100
    Robot.MoveC(PoseGrasp)

    ##################

    Robot.MoveC(PosePlace)
    PosePlace[2] = PosePlace[2]-100
    Robot.MoveC(PosePlace)
    Robot.ActuateGripper(30)
    PosePlace[2] = PosePlace[2]+100
    Robot.MoveC(PosePlace)
    Robot.Home()


def VisionBasedControl(Robot, NeuralNetworkModel, Move: str, ORIENTATION, ChessPieces, ScalerX, ScalerY):
    """
    Main Function for Vision-Based-Control. Currently only moving a chess piece from one position to another is supported / implemented.
    possible Solutions for Moves with multiple piece movement (e.g. capturing an opponent's piece):
    Extract amount of movements (1 movement equals picking & placing a piece) and loop through these movements
    """
    graspInput, placeInput, heights, flag = ProcessMove(Move, ChessPieces)

    graspOutput = ProcessInput(NeuralNetworkModel, graspInput, ScalerX, ScalerY, 'normal')
    placeOutput = ProcessInput(NeuralNetworkModel, placeInput, ScalerX, ScalerY, flag)

    MakeMove(Robot, graspOutput, placeOutput, ORIENTATION, heights)


if __name__ == '__main__':
    VisionBasedControl(None, None, 'e2e4', None, None, None, None)