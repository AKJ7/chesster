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
import time as time
import sys as sys
import os as os
sys.path.append(os.path.dirname(sys.path[0])) #preperation for import of custom moduls
from moduls.GenericSysFunctions import Printtimer, ImportCSV, ExportCSV, ChooseFolder #Import of custom moduls
from moduls.ImageProcessing import ExtractImageCoordinates
from camera.realSense import RealSenseCamera
from Robot.UR10 import UR10Robot
from Robot import robotiq_gripper
import imutils as imutils
from time import sleep
import urx as urx
import numpy as np

def HSV_Color_Selector(images):
    def nothing(x):
        pass
    # Create a window
    cv.namedWindow('image')
    cv.namedWindow('Slider')
    cv.resizeWindow('Slider', 640, 240)
    

    # Create trackbars for color change
    # Hue is from 0-179 for Opencv
    cv.createTrackbar('HMin', 'Slider', 0, 179, nothing)
    cv.createTrackbar('SMin', 'Slider', 0, 255, nothing)
    cv.createTrackbar('VMin', 'Slider', 0, 255, nothing)
    cv.createTrackbar('HMax', 'Slider', 0, 179, nothing)
    cv.createTrackbar('SMax', 'Slider', 0, 255, nothing)
    cv.createTrackbar('VMax', 'Slider', 0, 255, nothing)

    # Set default value for Max HSV trackbars
    cv.setTrackbarPos('HMax', 'Slider', 179)
    cv.setTrackbarPos('SMax', 'Slider', 255)
    cv.setTrackbarPos('VMax', 'Slider', 255)

    # Initialize HSV min/max values
    hMin = sMin = vMin = hMax = sMax = vMax = 0
    phMin = psMin = pvMin = phMax = psMax = pvMax = 0

    while(1):
        # Get current positions of all trackbars
        hMin = cv.getTrackbarPos('HMin', 'Slider')
        sMin = cv.getTrackbarPos('SMin', 'Slider')
        vMin = cv.getTrackbarPos('VMin', 'Slider')
        hMax = cv.getTrackbarPos('HMax', 'Slider')
        sMax = cv.getTrackbarPos('SMax', 'Slider')
        vMax = cv.getTrackbarPos('VMax', 'Slider')

        # Set minimum and maximum HSV values to display
        lower = np.array([hMin, sMin, vMin])
        upper = np.array([hMax, sMax, vMax])
        results = []
        # Convert to HSV format and color threshold
        for i in range(3):
            hsv = cv.cvtColor(images[i], cv.COLOR_BGR2HSV)
            mask = cv.inRange(hsv, lower, upper)
            result = cv.bitwise_and(images[i], images[i], mask=mask)
            results.append(result)
        # Display result image
        results = np.hstack((results[0], results[1], results[2]))
        cv.imshow('image', results)
        if cv.waitKey(10) & 0xFF == ord('q'):
            break

    cv.destroyAllWindows()
    return upper, lower
    

def GraspCali(Robot, Flag):
    if Flag == "y":
        TCP_Offset = 11 #taking TCP Configuration offset into account for grasping Calibration Object
        print('Grasping Calibration Object with offset 11mm in y-axis')
    else:
        TCP_Offset = 0
        print('Grasping Calibration Object without offset in y-axis')
    Robot.MoveC(np.array([-332.02, -540.5-TCP_Offset, 250, 0.012, -3.140, 0.023])) #WICHTIG: BASIS KOORDINATENSYSTEM!!
    Robot.MoveC(np.array([-332.02, -540.5-TCP_Offset, 22.5, 0.012, -3.140, 0.023]))
    Robot.CloseGripper()
    Robot.MoveC(np.array([-332.02, -540.5-TCP_Offset, 250, 0.012, -3.140, 0.023]))
    Robot.Home()   

def RemoveCali(Robot, Flag):
    if Flag == "y":
        TCP_Offset = 11 #taking TCP Configuration offset into account for grasping Calibration Object
    else:
        TCP_Offset = 0
    Robot.MoveC(np.array([-332.02, -540.5-TCP_Offset, 250, 0.012, -3.140, 0.023])) #WICHTIG: BASIS KOORDINATENSYSTEM!!
    Robot.MoveC(np.array([-332.02, -540.5-TCP_Offset, 22.5, 0.012, -3.140, 0.023]))
    Robot.OpenGripper()
    Robot.MoveC(np.array([-332.02, -540.5-TCP_Offset, 250, 0.012, -3.140, 0.023]))
    Robot.Home()

def TCPDetectionCheck(Color, Lower_Limit, Upper_Limit, Camera, Robot, RandomSample, Orientation):
    print("Initializing TCP Detection Checkup...")
    Printtimer(2)
    while True:
        print("current Color settings are:")
        print("------------------------------------------")
        print(f"Color HSV Values: {Color}")
        print(f"Upper Limit HSV Values: {Upper_Limit}")
        print(f"Lower Limit HSV Values: {Lower_Limit}")
        print("------------------------------------------")
        print("taking Pictures..")
        Pose = np.zeros((6))
        Imgs = []
        Imgs_Old = []
        for i in range(3):
            Pose[0:3] = RandomSample[0:3, i]
            Pose[3:6] = Orientation 
            Robot.MoveC(Pose)
            depth_image, c_img, _ = TakePicture(Camera)
            c_img_old = c_img.copy()
            _, c_img, _ = ExtractImageCoordinates(c_img, depth_image, Upper_Limit, Lower_Limit)
            c_img = cv.resize(c_img, (int(c_img.shape[0]*0.66), int(c_img.shape[1]*0.66)))
            c_img_old = cv.resize(c_img_old, (int(c_img.shape[0]*0.66), int(c_img.shape[1]*0.66)))
            Imgs.append(c_img)
            Imgs_Old.append(c_img_old)
        Imgs_stack = np.hstack((Imgs[0], Imgs[1], Imgs[2]))
        Imgs_Old_stack = np.hstack((Imgs_Old[0], Imgs_Old[1], Imgs_Old[2]))
        cv.namedWindow('Processed Images', cv.WINDOW_AUTOSIZE)
        cv.imshow('Processed Images', Imgs_stack)
        cv.waitKey(0)

        bool_flag = input("Do you want to adjust the limits? y/n: ")
        cv.destroyAllWindows()
        if (bool_flag=="y"):
            Upper_Limit, Lower_Limit = HSV_Color_Selector(Imgs_Old)
            #Llstr = input("Enter the three hsv values for the lower limit, seperated with ',': ")
            #Ulstr = input("Enter the three hsv values for the upper limit, seperated with ',': ")
            #Lower_Limit = np.fromstring(Llstr, dtype=int, sep=",")
            #Upper_Limit = np.fromstring(Ulstr, dtype=int, sep=",")
        else:
            break
    return Color, Lower_Limit, Upper_Limit

def SaveImage(ImgDir, Name, Image, Format=".bmp", ):
    cv.imwrite(ImgDir+"/"+Name+Format, Image)

def PointGeneration(n, xmin, xmax, ymin, ymax, zmin, zmax, height_Flag):
    RandomSample = np.zeros((3,n))
    x_rand = np.random.randint(xmin, xmax+1, n)
    y_rand = np.random.randint(ymin, ymax+1, n)
    if height_Flag == 'y':
        z_rand = 120
    else:
        z_rand = np.random.randint(zmin, zmax+1, n)
    RandomSample[0, :] = x_rand
    RandomSample[1, :] = y_rand
    RandomSample[2, :] = z_rand
    return RandomSample

def TrainingDataProcedure(n, RandomSample, DirOut, Flag_Images, Camera, Robot, Orientation, TRAINING_HOME, TRAINING_HOME_Init, Color_Upper_Limit, Color_Lower_Limit):
    ImgDir = DirOut+"/Images"
    Timestamp = time.time()
    ImgDir = ImgDir+str(Timestamp)
    #SAFEPOS = np.array([0, -720, 110, 0, 2.220, -2.220])
    os.mkdir(ImgDir, 0o666)
    Pose = np.zeros((6))
    
    Robot.MoveJ(TRAINING_HOME)
    Output = np.zeros((3, n)) #Shape: X
                              #       Y
                              #       Z
    Input = np.zeros((3, n))  #Shape: Img_X
                              #       Img_Y
                              #       Depth@XY
    start_total = time.time()
    for i in range(n):
        start = time.time()
        Pose[0:3] = RandomSample[0:3, i]
        Pose[3:6] = Orientation
        #Robot.MoveTrain(Pose, SAFEPOS, velocity=0.8, acceleration=0.15, rad=0.01)
        #Robot.MoveC(SAFEPOS, velocity=0.8, acceleration=0.3)
        Robot.MoveC(Pose) #With 60% Speed around 3 images are taken in 10 sec -> ~ 180 Images in 10 Minutes
        d_img, c_img, img_stack_cd = TakePicture(Camera)

        Input[0:3, i], img_proc, img_stack_mproc = ProcessInput(d_img, c_img.copy(), Color_Upper_Limit, Color_Lower_Limit)
        Output[0:3, i] = ProcessOutput(Robot)

        if(Flag_Images=="y"): #Show taken images
            cv.namedWindow('RealSense', cv.WINDOW_AUTOSIZE)
            cv.imshow('RealSense', img_stack_cd)
            cv.namedWindow('Processed Images', cv.WINDOW_AUTOSIZE)
            cv.imshow('Processed Images', img_stack_mproc)
            cv.waitKey(1)

        SaveImage(ImgDir, f"ImageC {i}", c_img)
        SaveImage(ImgDir, f"ImageD {i}", d_img)
        SaveImage(ImgDir, f"ImageProc {i}", img_proc)

        ExportCSV(Input, DirOut, f"Input{start_total}.csv", ";")
        ExportCSV(Output, DirOut, f"Output{start_total}.csv", ";")

        print(f"Input/Output {i+1} of {n} created")
        end = time.time()
        print(f"Time needed: {np.round(end-start,1)} sec.")
    end_total = time.time()
    Robot.MoveJ(TRAINING_HOME)
    Robot.MoveJ(TRAINING_HOME_Init)
    Robot.Home()

    print("-------------------------------------------------------------------------------------------")
    print(f"Script done! Training data set of {n}x Inputs/Outputs has been created.")
    print(f"Total time needed for data creation: {np.round(end_total-start_total,1)} sec.")
    print("-------------------------------------------------------------------------------------------")

def ProcessInput(depth_image, color_image, COLOR_UPPER_LIMIT, COLOR_LOWER_LIMIT): #Bright - Neon- Green is probably the best choice for Contour extraction of the TCP
    #testinput = np.array([np.random.randint(0,100,3)])
    Img_Coords, img_proc, img_stack_mproc = ExtractImageCoordinates(color_image, depth_image, COLOR_UPPER_LIMIT, COLOR_LOWER_LIMIT, ImageTxt="TCP")
    input = np.array([Img_Coords[0], Img_Coords[1], depth_image[Img_Coords[1]-1, Img_Coords[0]-1]]) #Flipped!
    return input, img_proc, img_stack_mproc

def ProcessOutput(Robot):
    Pose = np.array(Robot.WhereC())
    output = Pose[0:3]
    return output

def TakePicture(Camera):
    color_image = Camera.capture_color()
    time.sleep(0.3)
    depth_image = Camera.capture_depth() #depthimage is distance in meters

    #color_image = cv.cvtColor(color_image, cv.COLOR_RGB2BGR) #RealSense gives RGB, OpenCV takes BGR

    depth_colormap = cv.applyColorMap(cv.convertScaleAbs(depth_image, alpha=15), cv.COLORMAP_JET)
    images = np.hstack((color_image, depth_colormap))

    return depth_image, color_image, images

def main():
    print("This Script is about to produce a specified amount of pictures for training a neural network")
    print("initialisation...")
    Printtimer(1)

    IP_ADRESS="169.254.34.80"
    DIRPATH = os.path.dirname(__file__)
    #STANDARD_ORIENT = np.array([0, 2.220, -2.220])
    STANDARD_ORIENT = np.array([0.023, 2.387, -1.996])
    ARBEITSRAUM = ImportCSV(DIRPATH, "Arbeitsraum.csv" , ";")
    ARBEITSRAUM_MIN_MAX = ImportCSV(DIRPATH, "Arbeitsraum_min_max.csv" , ";")
    TRAINING_HOME_Init = np.array([0, -120, 120, 0, -90, -180]) #has to be called because the robot will otherwise crash into the camera
    TRAINING_HOME = np.array([60, -120, 120, 0, 90, 180])
    Color = np.array([350.1/2, 64, 71]) #currently hardcoded as bright neon green
    Color_Upper_Limit = np.array([179, 255, 255]) #Check https://stackoverflow.com/questions/10948589/choosing-the-correct-upper-and-lower-hsv-boundaries-for-color-detection-withcv for reference
    Color_Lower_Limit = np.array([167, 64, 111])
    print("Please choose your output directory for the taken images and files:")
    time.sleep(1)
    DIRPATH = os.path.dirname(__file__)
    DirOutput = DIRPATH+"/Trainingsdaten/"
    #DirOutput = ChooseFolder() #currently not working
    try:
        print("Trying to connect to UR10e...")
        UR10 = UR10Robot(Adress=IP_ADRESS)
    except Exception:
        print("Unable to connect to UR10e. Exception:")
        print(Exception)
        print("Please check for problems and restart this script.")
    else:
        print("Connection to UR10e successful.")
        try:
            print("Trying to connect to Intel RealSense D435...")
            RealSense = RealSenseCamera()
            #pipeline = rs.pipeline()
            #pipeline.start()
            #pipeline = "Test"
        except Exception:
            print("Unable to connect to Intel RealSense D435. Exception:")
            print(Exception)
            print("Please check for problems and restart this script.")
        else:
            print("Conenction to RealSense D435 successful, proceeding..")
            n_training = int(input("Please enter the amount of training data you would like to generate: "))
            height_Flag = input("Do you want to use a fixed height (Z-Coordinate)? y/n: ")
            TCP_Flag = input("Is the TCP configuration 'Chesster_train' activated? y/n: ")
            print("Grasping TCP Calibration Object...")
            GraspCali(UR10, TCP_Flag)
            print('Driving arm to Training Pose...')
            UR10.MoveJ(TRAINING_HOME_Init)
            UR10.MoveJ(TRAINING_HOME)
            RandomPoints = PointGeneration(n_training, ARBEITSRAUM_MIN_MAX[0,0], ARBEITSRAUM_MIN_MAX[0,1], ARBEITSRAUM_MIN_MAX[1,0], ARBEITSRAUM_MIN_MAX[1,1], ARBEITSRAUM_MIN_MAX[2,0], ARBEITSRAUM_MIN_MAX[2,1], height_Flag)
            bool_Images = input("Do you want to see the taken images? y/n: ")
            bool_Color_Correction = input("Do you want to check the TCP Detection Algorithm before proceeding with the data generation? y/n: ")
            if (bool_Color_Correction=="y"):
                Color, Color_Lower_Limit, Color_Upper_Limit = TCPDetectionCheck(Color, Color_Lower_Limit, Color_Upper_Limit, RealSense, UR10, RandomPoints, STANDARD_ORIENT)
            print("Initialization done!")
            print("Proceeding with training data generation...")
            print("----------------------------------------------------------------------------------------------------------")
            TrainingDataProcedure(n_training, RandomPoints, DirOutput, bool_Images, RealSense, UR10, STANDARD_ORIENT, TRAINING_HOME, TRAINING_HOME_Init, Color_Upper_Limit, Color_Lower_Limit)
            print("Placing Calibration-Object...")
            RemoveCali(UR10, TCP_Flag)
            print("Done.")
    finally:
        print("Cutting all connections...")
        UR10.stop()
        #RealSense.stop()
        cv.destroyAllWindows()
        print("Finished.")
if __name__ == "__main__":
    main()
    