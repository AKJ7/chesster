#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Author: Thorben Pultke
Contact: thorben.pultke@gmx.de
Project: CHESSter
Summary: Short script for implementing a automated training data generation 
to work with neural networks as mapping for image COS coords to robot COS coords.
"""
import tkinter as tk
from tkinter.filedialog import askdirectory
import cv2 as cv #OpenCV
import numpy as np
import urx as urx #UR10e Library for simple Movement
import pyrealsense2 as rs #Intel Realsense library for Camera Functions
import time as time
import sys as sys
import csv as csv

import os as os
import threading as th
sys.path.append(os.path.dirname(sys.path[0])) #preperation for import of custom moduls
from SystemRelatedFunctions.GenericSysFunctions import Printtimer, ImportCSV, ExportCSV, ChooseFolder #Import of custom moduls

from winrt import _winrt


def PointGeneration(n, xmin, xmax, ymin, ymax, zmin, zmax):
    RandomSample = np.zeros((3,n))
    x_rand = np.random.randint(xmin, xmax+1, n)
    y_rand = np.random.randint(ymin, ymax+1, n)
    z_rand = np.random.randint(zmin, zmax+1, n)
    RandomSample[0, :] = x_rand
    RandomSample[1, :] = y_rand
    RandomSample[2, :] = z_rand
    return RandomSample

def TrainingProcedure(n, RandomSample, DirOut, Flag_Images, pipeline, Robot, Orientation, HOME, TRAINING_HOME):
    ImgDir = DirOut+"/Images"
    Timestamp = time.time()
    ImgDir = ImgDir+str(Timestamp)
    os.mkdir(ImgDir, 0o666)
    Pose = np.zeros((6))
    Robot.movej(TRAINING_HOME, vel=0.6)
    Output = np.zeros((3, n)) #Shape: X
                              #       Y
                              #       Z
    Input = np.zeros((3, n))  #Shape: Img_X
                              #       Img_Y
                              #       DepthXY
    start_total = time.time()
    for i in range(n):
        start = time.time()
        Pose[0:3] = RandomSample[0:3, i]/1000 #Konvertierung in Meter
        Pose[3:6] = Orientation
        #if(True):
        if(Robot.is_running()):
            Robot.movel(Pose, vel=0.6, acc=0.15)
            d_img, c_img = TakePicture(pipeline, Flag_Images, ImgDir, i)

            Input[0:3, i] = ProcessInput(d_img, c_img)
            Output[0:3, i] = ProcessOutput(Robot)

            print(f"Input/Output {i+1} from {n} created")
            #Robot.movej(HOME, vel=0.3)
            end = time.time()
            print(f"Time needed: {np.round(end-start,1)} sec.")

        else:
            print("Robot lost connection. Please check all connections and restart this script.")
    end_total = time.time()
    Robot.movej(HOME, vel=0.5, acc=0.15)
    ExportCSV(Input, DirOut, "Input.csv", ";")
    ExportCSV(Output, DirOut, "Output.csv", ";")
    print("-------------------------------------------------------------------------------------------")
    print(f"Script done! {n} training data has been created.")
    print(f"Total time needed for data creation: {np.round(end_total-start_total,1)} sec.")
    print("-------------------------------------------------------------------------------------------")

def ProcessInput(depth_image, color_image):
    testinput = np.array([np.random.randint(0,100,3)])
    return testinput

def ProcessOutput(Robot):
    Pose = np.array(Robot.getl())
    testoutput = np.round(Pose[0:3]*1000,1)
    return testoutput

def TakePicture(pipeline, Flag_Images, ImgDir, i):
    frames = pipeline.wait_for_frames()
    depth_frame = frames.get_depth_frame()
    color_frame = frames.get_color_frame()
    depth_image = np.asanyarray(depth_frame.get_data())
    color_image = np.asanyarray(color_frame.get_data())

    color_image = cv.cvtColor(color_image, cv.COLOR_RGB2BGR) #RealSense gives RGB, OpenCV takes BGR

    depth_colormap = cv.applyColorMap(cv.convertScaleAbs(depth_image, alpha=0.03), cv.COLORMAP_JET)
    images = np.hstack((color_image, depth_colormap))

    if(Flag_Images=="y"): #Show taken images
        cv.namedWindow('RealSense', cv.WINDOW_AUTOSIZE)
        cv.imshow('RealSense', images)
        cv.waitKey(2)
    ImgNameColor = f"/ImageC {i}.bmp"
    ImgNameDepth = f"/ImageD {i}.bmp"
    cv.imwrite(ImgDir+ImgNameColor, color_image)
    cv.imwrite(ImgDir+ImgNameDepth, depth_image)
    return depth_image, color_image

def main():
    print("This Script is about to produce a specified amount of pictures for training a neural network")
    print("initialisation...")
    Printtimer(1)

    IP_ADRESS="169.254.34.80"
    DIRPATH = os.path.dirname(__file__)
    STANDARD_ORIENT = np.array([4.712, 0.011, -0.001]) #Standard Pitch, Yaw, Roll angles for training data generation -> tbd
    ARBEITSRAUM = ImportCSV(DIRPATH, "Arbeitsraum.csv" , ";")
    ARBEITSRAUM_MIN_MAX = ImportCSV(DIRPATH, "Arbeitsraum_min_max.csv" , ";")
    HOME_DEG = np.array([90, -120, 120, -180, -90, 0])
    HOME_RAD = np.deg2rad(HOME_DEG)
    TRAINING_HOME_DEG = np.array([90, -120, 120, 0, -90, -180])
    TRAINING_HOME_RAD = np.deg2rad(TRAINING_HOME_DEG)
    print("Please choose your output directory for the taken images and files:")
    time.sleep(1)
    DirOutput = "C:/Users/admin/Desktop/ML/chesster/chesster/Vision-Based-Control/Trainingsdaten"
    #DirOutput = ChooseFolder() #currently not working
    try:
        print("Trying to connect to UR10e...")
        UR10 = urx.Robot(IP_ADRESS)
        #UR10 = "Test"
    except Exception:
        print("Unable to connect to UR10e. Exception:")
        print(Exception)
        print("Please check for problems and restart this script.")
    else:
        print("Conenction to UR10e successful, moving to home position...")
        UR10.movej(HOME_RAD, vel=0.6, acc=0.15)
        print("Movement succefull! Proceeding...")
        try:
            print("Trying to connect to Intel RealSense D435...")
            pipeline = rs.pipeline()
            pipeline.start()
            #pipeline = "Test"
        except Exception:
            print("Unable to connect to Intel RealSense D435. Exception:")
            print(Exception)
            print("Please check for problems and restart this script.")
        else:
            print("Conenction to RealSense D435 successful, proceeding..")
            n_training = int(input("Please enter the amount of training data you would like to generate: "))
            bool_Images = input("Do you want to see the taken images? y/n: ")
            print("Generating RandomPoints...")
            RandomPoints = PointGeneration(n_training, ARBEITSRAUM_MIN_MAX[0,0], ARBEITSRAUM_MIN_MAX[0,1], ARBEITSRAUM_MIN_MAX[1,0], ARBEITSRAUM_MIN_MAX[1,1], ARBEITSRAUM_MIN_MAX[2,0], ARBEITSRAUM_MIN_MAX[2,1])
            print("Initialization done!")
            print("Proceeding with training data generation...")
            print("----------------------------------------------------------------------------------------------------------")
            TrainingProcedure(n_training, RandomPoints, DirOutput, bool_Images, pipeline, UR10, STANDARD_ORIENT, HOME_RAD, TRAINING_HOME_RAD)

    finally:
        print("Cutting all connections...")
        UR10.stop()
        pipeline.stop()
        cv.destroyAllWindows()
        print("Finished.")
if __name__ == "__main__":
    main()
    