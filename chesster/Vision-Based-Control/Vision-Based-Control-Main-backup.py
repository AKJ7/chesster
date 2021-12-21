import sys as sys
import os as os
sys.path.append(os.path.dirname(sys.path[0])) #preperation for import of custom moduls
from moduls.ImageProcessing import ExtractImageCoordinates, FigureMapping
import tensorflow as tf
import keras as keras
import numpy as np
import cv2 as cv

def ProcessMove(Move: str):
    GraspArray = np.array([]) #Shape: [ImageMatrixRow, ImageMatrixCol] -> Gets the corresponding Imagepart for Grabbing
    PlaceArray = np.array([]) #Shape: [ImageMatrixRow, ImageMatrixCol] -> Gets the corresponding Imagepart for placement 
    Piece = "Springer"#HIER STRING CHECKUP EINBRINGEN
    return GraspArray, PlaceArray, Piece

def ProcessInput(NeuralNetworkModel, Input):
    Output = np.array([])
    return Output

def Convert2WholeImage(c_img_meta, Row, Col, Coordinates: np.array):
    height_meta = c_img_meta[Row, Col, 0] #Matrix wird gebraucht, in denen die koordinaten des geslicten Images drin stehen
    width_meta = c_img_meta[Row, Col, 1] #damit eine Zurückrechnung auf das gesamte Bild möglich ist.
    Coordinates[0] = width_meta + Coordinates[0]
    Coordinates[1] = height_meta + Coordinates[1]
    return Coordinates

def ExtractImageCoordinates_EmptyField(c_img, c_img_meta, PlaceArray):
    height_img = c_img.shape[0]
    width_img = c_img.shape[1]
    pxCords = np.array([height_img, width_img])
    return pxCords

def VisionBasedControl(Robot, NeuralNetworkModel, Img_Matrix, depth_img, c_img, c_img_meta, Move: str, ORIENTATION):
    """
    Main Function for Vision-Based-Control. Currently only moving a chess piece from one position to another is supported / implemented.
    possible Solutions for Moves with multiple piece movement (e.g. capturing an opponent's piece):
    Extract amount of movements (1 movement equals picking & placing a piece) and loop through these movements
    """
#def VisionBasedControl():
    #FigureColorMapping = FigureMapping(os.path.dirname(__file__), "Farbmapping.csv")
    GraspIndeces, PlaceIndeces, Piece = ProcessMove(Move)
    #Index = int(np.where(FigureColorMapping==Piece)[0])

    Input_Grasp = np.zeros((3))
    Input_Place = np.zeros((3))
    Output_Grasp = np.zeros((6))
    Output_Place = np.zeros((6))

    Input_Grasp[0:2], _, images = ExtractImageCoordinates(Img_Matrix[GraspIndeces[0]][GraspIndeces[1]], FigureColorMapping[Index, 1], FigureColorMapping[Index, 2], ImageTxt=FigureColorMapping[Index, 0])
    Input_Place[0:2] = ExtractImageCoordinates_EmptyField(Img_Matrix[GraspIndeces[0]][GraspIndeces[1]], c_img_meta, PlaceIndeces)
    
    Input_Grasp[0:2] = Convert2WholeImage(c_img_meta, Img_Matrix[GraspIndeces[0]], Img_Matrix[GraspIndeces[1]], Input_Grasp[0:2])
    Input_Place[0:2] = Convert2WholeImage(c_img_meta, Img_Matrix[PlaceIndeces[0]], Img_Matrix[GraspIndeces[1]], Input_Place[0:2])
    
    Input_Grasp[2] = depth_img[Input_Grasp[0], Input_Grasp[1]]
    Input_Place[2] = depth_img[Input_Place[0], Input_Place[1]]

    Output_Grasp[0:3] = ProcessInput(NeuralNetworkModel, Input_Grasp)
    Output_Place[0:3] = ProcessInput(NeuralNetworkModel, Input_Place)

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