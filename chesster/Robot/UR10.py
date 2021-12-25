import urx as urx
from urx.robotiq_two_finger_gripper import Robotiq_Two_Finger_Gripper #URX Class for Robotiq Gripper
import numpy as np
from pathlib import Path
from time import sleep
class UR10Robot:
    def __init__(self, Adress: str = "169.254.34.80"):
        self.__UR10 = urx.Robot(Adress, )
        self.__Gripper = Robotiq_Two_Finger_Gripper(self.__UR10, socket_host="169.254.34.1")
        if not self.__UR10.is_running():
            # Exception in Constructor ...
            raise RuntimeError("Couldn't connect to UR10. Check remote control and power status.")
        self.__homepos = np.array([90, -120, 120, -180, -90, 0])
        self.__vel: float = 0.6
        self.__acc: float = 0.15
        self.__start()

    def __start(self):
        self.Home()
        sleep(1)
        self.CloseGripper()
        sleep(1)
        self.OpenGripper()

    def __del__(self):
        self.__UR10.stop()

    def stop(self):
        self.__UR10.stop()

    def Home(self):
        """
        Moves the robot to it's designated home position (Default: {90, -120, 120, 0, -90, -180} in joint space).
        """
        home = self.cDeg2Rad(self.__homepos)
        self.__UR10.movej(home, acc=self.__acc, vel=self.__vel)

    def MoveJ(self, PoseJ: np.array):
        """
        Pass the joint pose the robot should approach in degree. 
        """
        self.CheckStatus(cmd='Move in Joint Space')
        PoseJ = self.cDeg2Rad(PoseJ)
        self.__UR10.movej(PoseJ, acc=self.__acc, vel=self.__vel)

    def MoveC(self, PoseC: np.array):
        """
        Pass the cartesian pose the robot should approach in millimeters and the expected orientation of the TCP in radians. 
        """
        self.CheckStatus(cmd='Move in Cartesian Space')
        PoseC[0:3] = PoseC[0:3]/1000
        self.__UR10.movel(PoseC, acc=self.__acc, vel=self.__vel)
    
    def MoveTrain(self, PoseC: np.array, PoseSafe: np.array, rad=0.01, velocity=0.6, acceleration=0.15):
        """
        Pass the cartesian pose the robot should approach in millimeters and the expected orientation of the TCP in radians. This Move
        method is especially designed for the training procedure since it always drives to a safe position with transition to its new pos.
        """
        self.CheckStatus(cmd='Move in Cartesian Space')
        PoseSafe[0:3] = PoseSafe[0:3]/1000
        PoseC[0:3] = PoseC[0:3]/1000
        Poses = [PoseSafe, PoseC]
        self.__UR10.movels(Poses, acc=acceleration, vel=velocity, radius=rad)

    def WhereJ(self):
        """
        Returns the current pose in joint space in Degree.
        """
        self.CheckStatus(cmd='Return Pose in Joint Space')
        Pose = np.array(self.__UR10.getj())
        Pose = self.cRad2Deg(Pose)
        return Pose

    def WhereC(self):
        """
        Returns the current pose in cartesian space in millimeters and orientation in radians.
        """
        self.CheckStatus(cmd='Return Pose in Cartesian Space')
        Pose = np.array(self.__UR10.getl())
        Pose[0:3] = np.round(Pose[0:3]*1000,1) #Converting Cartesian Coords from meter to millimeter
        return Pose

    def cDeg2Rad(self, Array: np.array):
        """
        Converts Degree to Radian.
        """
        Array = np.deg2rad(Array)
        return Array

    def cRad2Deg(self, Array: np.array):
        """
        Converts Radian to Degree.
        """
        Array = np.rad2deg(Array)
        return Array

    def OpenGripper(self):
        """
        Open the Robotiq two finger gripper completly -> Val = 0
        """
        self.__Gripper.open_gripper()

    def CloseGripper(self):
        """
        Closes the Robotiq two finger gripper completly -> Val = 255
        """
        self.__Gripper.close_gripper()

    def ActuateGripper(self, value: int):
        """
        Moves the Robotiq gripper fingers to a specified value. 0 equals completly open, 255 equals completly closed.
        """
        self.__Gripper.gripper_action(value)

    def CheckStatus(self, cmd: str):
        """
        Checks whether the Robot is still connected or not and raises an Exception
        """
        if not self.__UR10.is_running():
            raise RuntimeError(f"UR10 lost connection. Could not process command: {cmd}")


