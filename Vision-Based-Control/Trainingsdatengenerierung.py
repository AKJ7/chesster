import cv2 as cv #OpenCV
import numpy as np
import urx as urx #UR10e Library for simple Movement
import pyrealsense2 as rs #Intel Realsense library for Camera Functions
import time as time
import sys as sys
import csv as csv

from SystemRelatedFunctions.GenericSysFunctions import Printtimer



def main():
    print("This Script is about to produce a specified amount of pictures for training a neural network")
    print("initialisation...")
    Printtimer(5)


if __name__ == "__main__":
    main()