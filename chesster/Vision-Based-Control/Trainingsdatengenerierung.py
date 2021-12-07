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
from SystemRelatedFunctions.GenericSysFunctions import Printtimer, ImportCSV, ExportCSV, ChooseFolder #Import of custom moduls

def PointGeneration(n, xmin, xmax, ymin, ymax, zmin, zmax):
    RandomSample = np.zeros((3,n))
    x_rand = np.random.randint(xmin, xmax+1, n)
    y_rand = np.random.randint(ymin, ymax+1, n)
    z_rand = np.random.randint(zmin, zmax+1, n)
    RandomSample[0, :] = x_rand
    RandomSample[1, :] = y_rand
    RandomSample[2, :] = z_rand
    return RandomSample

def TrainingProcedure(n, RandomSample, DirOut, Flag_Images, pipeline, Robot, Orientation):
    ImgDir = DirOut+"/Images"
    os.mkdir(ImgDir, 0o666)
    Pose = np.zeros((1,6))
    Output = np.zeros((3, n)) #Shape: X
                              #       Y
                              #       Z
    Input = np.zeros((3, n))  #Shape: Img_X
                              #       Img_Y
                              #       DepthXY
    
    for i in range(n):
        Pose[0:3] = RandomSample[0:3, i]
        Pose[3:6] = Orientation
        if(Robot.is_running()):
            Robot.movel(Pose)
            d_img, c_img = TakePicture(pipeline, Flag_Images, ImgDir, i)

            Input[0:3, i] = ProcessInput(d_img, c_img)
            Output[0:3, i] = ProcessOutput(Robot)

            print(f"Input/Output {i} from {n} created")
        else:
            print("Robot lost connection. Please check all connections and restart this script.")

def ProcessInput(depth_image, color_image):
    testinput = np.array([np.random.randint(0,100,3)])
    return testinput

def ProcessOutput(Robot):
    Pose = Robot.getl()
    testoutput = np.array(Pose[0:3])
    return testoutput

def TakePicture(pipeline, Flag_Images, ImgDir, i):
    frames = pipeline.wait_for_frames()
    depth_frame = frames.get_depth_frame()
    color_frame = frames.get_color_frame()
    depth_image = np.asanyarray(depth_frame.get_data())
    color_image = np.asanyarray(color_frame.get_data())

    depth_colormap = cv.applyColorMap(cv.convertScaleAbs(depth_image, alpha=0.03), cv.COLORMAP_JET)
    images = np.hstack((color_image, depth_colormap))

    if(Flag_Images=="y"): #Show taken images
        cv.namedWindow('RealSense', cv.WINDOW_AUTOSIZE)
        cv.imshow('RealSense', images)
        cv.waitKey(2)
    ImgNameColor = f"ImageC {i}.bmp"
    ImgNameDepth = f"ImageC {i}.bmp"
    cv.imwrite(ImgDir+ImgNameColor, color_image)
    cv.imwrite(ImgDir+ImgNameDepth, depth_image)
    return depth_image, color_image

def main():
    print("This Script is about to produce a specified amount of pictures for training a neural network")
    print("initialisation...")
    Printtimer(1)

    IP_ADRESS="XXX.XXX.XXX.XXX"
    DIRPATH = os.path.dirname(__file__)
    STANDARD_ORIENT = np.array([90, 90, 90]) #Standard Pitch, Yaw, Roll angles for training data generation -> tbd
    ARBEITSRAUM = ImportCSV(DIRPATH, "Arbeitsraum.csv" , ";")
    ARBEITSRAUM_MIN_MAX = ImportCSV(DIRPATH, "Arbeitsraum_min_max.csv" , ";")

    print("Please choose your output directory for the taken images and files:")
    time.sleep(2)
    DirOutput = ChooseFolder()

    try:
        print("Trying to connect to UR10e...")
        UR10 = urx.Robot(IP_ADRESS)
    except Exception:
        print("Unable to connect to UR10e. Exception:")
        print(Exception)
        print("Please check for problems and restart this script.")
    else:
        print("Conenction to UR10e successful, proceeding..")
        try:
            print("Trying to connect to Intel RealSense D435...")
            pipeline = rs.pipeline()
            pipeline.start()
        except Exception:
            print("Unable to connect to Intel RealSense D435. Exception:")
            print(Exception)
            print("Please check for problems and restart this script.")
        else:
            print("Conenction to RealSense D435 successful, proceeding..")
            n_training = input("Please enter the amount of training data you would like to generate: ")
            bool_Images = input("Do you want to see the taken images? y/n: ")
            print("Generating RandomPoints...")
            RandomPoints = PointGeneration(n_training, ARBEITSRAUM_MIN_MAX[0,0], ARBEITSRAUM_MIN_MAX[0,1], ARBEITSRAUM_MIN_MAX[1,0], ARBEITSRAUM_MIN_MAX[1,1], ARBEITSRAUM_MIN_MAX[2,0], ARBEITSRAUM_MIN_MAX[2,1])
            print("Initialization done!")
            print("Proceeding with training data generation...")
            print("----------------------------------------------------------------------------------------------------------")
            TrainingProcedure(n_training, RandomPoints, DirOutput, bool_Images, pipeline, UR10, STANDARD_ORIENT)

    finally:
        UR10.stop()
        pipeline.stop()
if __name__ == "__main__":
    main()
    