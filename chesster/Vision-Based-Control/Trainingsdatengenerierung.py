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
from SystemRelatedFunctions.GenericSysFunctions import Printtimer, ImportCSV, ExportCSV, ChooseFolder #Import of custom moduls
from camera.realSense import RealSenseCamera
from Robot.UR10 import UR10Robot
import imutils as imutils

def GraspCali(Robot):
    !Robot.MoveJ([])
    Robot.CloseGripper()
    Robot.Home()

def TCPDetectionCheck(Color, Lower_Limit, Upper_Limit, Camera):
    print("Initializing TCP Detection Checkup...")
    Printtimer(2)
    while True:
        print("current Color settings are:")
        print("------------------------------------------")
        print(f"Color HSV Values: {Color}")
        print(f"Upper Limit HSV Values: {Upper_Limit}")
        print(f"Lower Limit HSV Values: {Lower_Limit}")
        print("------------------------------------------")
        print("taking Picture..")
        
        _, c_img, _ = TakePicture(Camera)
        _, _, img_stack = ExtractImageCoordinates(c_img, Color, Upper_Limit, Lower_Limit)

        cv.namedWindow('Processed Images', cv.WINDOW_AUTOSIZE)
        cv.imshow('Processed Images', img_stack)
        cv.waitKey(0)

        bool_flag = input("Do you want to adjust the limits? y/n: ")
        if (bool_flag=="y"):
            Llstr = input("Enter the three hsv values for the lower limit, seperated with ',': ")
            Ulstr = input("Enter the three hsv values for the upper limit, seperated with ',': ")
            Lower_Limit = np.fromstring(Llstr, dtype=int, sep=",")
            Upper_Limit = np.fromstring(Ulstr, dtype=int, sep=",")
        else:
            break
    return Color, Lower_Limit, Upper_Limit

def SaveImage(ImgDir, Name, Image, Format=".bmp", ):
    cv.imwrite(ImgDir+"/"+Name+Format, Image)

def PointGeneration(n, xmin, xmax, ymin, ymax, zmin, zmax):
    RandomSample = np.zeros((3,n))
    x_rand = np.random.randint(xmin, xmax+1, n)
    y_rand = np.random.randint(ymin, ymax+1, n)
    z_rand = np.random.randint(zmin, zmax+1, n)
    RandomSample[0, :] = x_rand
    RandomSample[1, :] = y_rand
    RandomSample[2, :] = z_rand
    return RandomSample

def TrainingDataProcedure(n, RandomSample, DirOut, Flag_Images, Camera, Robot, Orientation, TRAINING_HOME):
    ImgDir = DirOut+"/Images"
    Timestamp = time.time()
    ImgDir = ImgDir+str(Timestamp)
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
        #if(True):
        if(Robot.is_running()):
            Robot.MoveC(Pose) #With 60% Speed around 3 images are taken in 10 sec -> ~ 180 Images in 10 Minutes
            d_img, c_img, img_stack_cd = TakePicture(Camera, ImgDir, i)

            Input[0:3, i], img_proc, img_stack_mproc = ProcessInput(d_img, c_img)
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

            print(f"Input/Output {i+1} from {n} created")
            #Robot.MoveJ(TRAINING_HOME)
            end = time.time()
            print(f"Time needed: {np.round(end-start,1)} sec.")

        else:
            print("Robot lost connection. Please check all connections and restart this script.")
    end_total = time.time()
    Robot.Home()
    ExportCSV(Input, DirOut, "Input.csv", ";")
    ExportCSV(Output, DirOut, "Output.csv", ";")
    print("-------------------------------------------------------------------------------------------")
    print(f"Script done! {n} training data has been created.")
    print(f"Total time needed for data creation: {np.round(end_total-start_total,1)} sec.")
    print("-------------------------------------------------------------------------------------------")

def ExtractImageCoordinates(color_image, COLOR, COLOR_UPPER_LIMIT, COLOR_LOWER_LIMIT):
    hsv_image = cv.cvtColor(color_image, cv.COLOR_BGR2HSV) #Colordetection works better with hsv space
    mask = cv.inRange(hsv_image, COLOR_LOWER_LIMIT, COLOR_UPPER_LIMIT)

    cv.imshow(f"Masked Image", mask)
    cnts = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    for c in cnts:
        M = cv.moments(c)
        area = cv.contourArea(c)
        if (area >= 20):
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            #print(f"Centerpoint {i} painted")
            cv.drawContours(color_image, [c], -1, [0, 0, 255], 2)
            cv.circle(color_image, (cX,cY), 3, [0, 0, 255], -1)
            cv.putText(color_image, "TCP", (cX-20, cY-20), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            PxCoords = np.array([cX, cY])
    images = np.hstack((mask, color_image))
    return PxCoords, color_image, images

def ProcessInput(depth_image, color_image, COLOR, COLOR_UPPER_LIMIT, COLOR_LOWER_LIMIT): #Bright - Neon- Green is probably the best choice for Contour extraction of the TCP
    #testinput = np.array([np.random.randint(0,100,3)])
    Img_Coords, img_proc, img_stack_mproc = ExtractImageCoordinates(color_image, COLOR, COLOR_UPPER_LIMIT, COLOR_LOWER_LIMIT)
    input = np.array([Img_Coords[0], Img_Coords[1], depth_image[Img_Coords[0], Img_Coords[1]]]) 
    return input, img_proc, img_stack_mproc

def ProcessOutput(Robot):
    Pose = np.array(Robot.WhereC())
    output = Pose[0:3]
    return output

def TakePicture(Camera):
    color_image = Camera.capture_color()
    depth_image = Camera.capture_depth() #depthimage is distance in meters

    #color_image = cv.cvtColor(color_image, cv.COLOR_RGB2BGR) #RealSense gives RGB, OpenCV takes BGR

    depth_colormap = cv.applyColorMap(cv.convertScaleAbs(depth_image, alpha=0.03), cv.COLORMAP_JET)
    images = np.hstack((color_image, depth_colormap))

    return depth_image, color_image, images

def main():
    print("This Script is about to produce a specified amount of pictures for training a neural network")
    print("initialisation...")
    Printtimer(1)

    IP_ADRESS="169.254.34.80"
    DIRPATH = os.path.dirname(__file__)
    STANDARD_ORIENT = np.array([4.712, 0.011, -0.001]) #Standard Pitch, Yaw, Roll angles for training data generation -> tbd
    ARBEITSRAUM = ImportCSV(DIRPATH, "Arbeitsraum.csv" , ";")
    ARBEITSRAUM_MIN_MAX = ImportCSV(DIRPATH, "Arbeitsraum_min_max.csv" , ";")
    TRAINING_HOME_DEG = np.array([90, -120, 120, 0, -90, -180])
    TRAINING_HOME_RAD = np.deg2rad(TRAINING_HOME_DEG)
    !Color = np.array([]) #currently hardcoded as bright neon green
    !Color_Upper_Limit = np.array([]) #Check https://stackoverflow.com/questions/10948589/choosing-the-correct-upper-and-lower-hsv-boundaries-for-color-detection-withcv for reference
    !Color_Lower_Limit = np.array([])
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
        print("Grasping TCP Calibration Object...")
        GraspCali(UR10)
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
            bool_Images = input("Do you want to see the taken images? y/n: ")
            bool_Color_Correction = input("Do you want to check the TCP Detection Algorithm before proceeding with the data generation? y/n: ")
            if (bool_Color_Correction=="y"):
                Color, Color_Lower_Limit, Color_Upper_Limit = TCPDetectionCheck(Color, Color_Lower_Limit, Color_Upper_Limit, RealSense)
                
            print("Generating RandomPoints...")
            RandomPoints = PointGeneration(n_training, ARBEITSRAUM_MIN_MAX[0,0], ARBEITSRAUM_MIN_MAX[0,1], ARBEITSRAUM_MIN_MAX[1,0], ARBEITSRAUM_MIN_MAX[1,1], ARBEITSRAUM_MIN_MAX[2,0], ARBEITSRAUM_MIN_MAX[2,1])
            print("Initialization done!")
            print("Proceeding with training data generation...")
            print("----------------------------------------------------------------------------------------------------------")
            TrainingDataProcedure(n_training, RandomPoints, DirOutput, bool_Images, RealSense, UR10, STANDARD_ORIENT, TRAINING_HOME_RAD)

    finally:
        print("Cutting all connections...")
        UR10.stop()
        RealSense.stop()
        cv.destroyAllWindows()
        print("Finished.")
if __name__ == "__main__":
    main()
    