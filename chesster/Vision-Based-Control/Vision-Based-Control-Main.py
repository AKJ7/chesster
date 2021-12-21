import sys as sys
import os as os
sys.path.append(os.path.dirname(sys.path[0])) #preperation for import of custom moduls
from moduls.ImageProcessing import ExtractImageCoordinates, FigureMapping
import tensorflow as tf
import keras as keras
import numpy as np
import cv2 as cv

def ProcessMove(Move: str):
    ALPHABET = ['a','b','c','d','e','f','g','h']
    if 'x' in Move:
        pass #Hier Ablauf für Schlagen einer Figur implementieren
    elif 'QQ' in Move:
        pass #Hier Ablauf für Bauernumwandlung

    else:
        Grasp = Move[0:2] #First part of move (grasp)
        Place = Move[2:4] #second part of move (place)

    return None

def ProcessInput(NeuralNetworkModel, Input):
    Output = np.array([])
    return Output

def VisionBasedControl(Robot, NeuralNetworkModel, ChessObj, Move: str, ORIENTATION):
    """
    Main Function for Vision-Based-Control. Currently only moving a chess piece from one position to another is supported / implemented.
    possible Solutions for Moves with multiple piece movement (e.g. capturing an opponent's piece):
    Extract amount of movements (1 movement equals picking & placing a piece) and loop through these movements
    """
#def VisionBasedControl():
    GraspIndeces, PlaceIndeces, Piece = ProcessMove(Move)

    Input_Grasp = np.zeros((3))
    Input_Place = np.zeros((3))
    Output_Grasp = np.zeros((6))
    Output_Place = np.zeros((6))

    Output_Grasp[2] = Output_Grasp[2]+20
    Output_Place[2] = Output_Place[2]+20

    Output_Grasp[3:6] = ORIENTATION
    Output_Place[3:6] = ORIENTATION

    Robot.MoveC(Output_Grasp)
    Output_Grasp[2] = Output_Grasp[2]-20
    Robot.CloseGripper()
    Robot.Home()
    Robot.MoveC(Output_Place)
    Output_Place[2] = Output_Place[2]-20
    Robot.MoveC(Output_Place)
    Robot.OpenGripper()
    Robot.Home()

if __name__ == '__main__':
    VisionBasedControl(None, None, None, None, None, None)