import cv2 as cv #OpenCV
import numpy as np
import urx as urx #UR10e Library for simple Movement
import pyrealsense2 as rs #Intel Realsense library for Camera Functions
import time as time
import sys as sys
import csv as csv

import os as os #preperation for import of custom moduls
sys.path.append(os.path.dirname(sys.path[0]))

from SystemRelatedFunctions.GenericSysFunctions import Printtimer, ImportCSV #Import of custom moduls

def main():
    print("This Script is about to produce a specified amount of pictures for training a neural network")
    print("initialisation...")
    Printtimer(1)

    path = os.path.dirname(__file__)

    Matrix = ImportCSV(path, "test.csv" , ";")

    print(Matrix)
if __name__ == "__main__":
    main()
    
    