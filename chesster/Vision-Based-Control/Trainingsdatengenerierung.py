#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Author: Thorben Pultke
Contact: thorben.pultke@gmx.de
Project: CHESSter
Summary: Short script for implementing a automated training data generation 
to work with neural networks as mapping for image COS coords to robot COS coords.
"""

import cv2 as cv #OpenCV
import numpy as np
import urx as urx #UR10e Library for simple Movement
import pyrealsense2 as rs #Intel Realsense library for Camera Functions
import time as time
import sys as sys
import csv as csv

import os as os

sys.path.append(os.path.dirname(sys.path[0])) #preperation for import of custom moduls
from SystemRelatedFunctions.GenericSysFunctions import Printtimer, ImportCSV, ExportCSV #Import of custom moduls



def main():
    print("This Script is about to produce a specified amount of pictures for training a neural network")
    print("initialisation...")
    Printtimer(1)

    IP_ADRESS="XXX.XXX.XXX.XXX"
    DIRPATH = os.path.dirname(__file__)

    Arbeitsraum = ImportCSV(DIRPATH, "Arbeitsraum.csv" , ";")
    UR10 = urx.Robot(IP_ADRESS)
if __name__ == "__main__":
    main()
    