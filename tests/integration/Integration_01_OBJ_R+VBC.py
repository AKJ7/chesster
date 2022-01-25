from chesster.vision_based_control.controller import VisualBasedController
from chesster.obj_recognition.chessboard_recognition import ChessBoard
from chesster.camera.realsense import RealSenseCamera
from chesster.Robot.UR10 import UR10Robot

if __name__ == "__main__":
    robot = UR10Robot()
    camera = RealSenseCamera()
    vbc = VisualBasedController(robot, "/")
    chessboard = ChessBoard()
    i=0
    move = ""
    print('####################################################################')
    print('Integration test 01: Integration of Object/Chessboard recognition')
    print('and Vision-Based-Control')
    print('####################################################################')
        
    while True:
        i=i+1
        print(f'Attempt {i}')
        print(f'## Move Examples ##')
        print(f'Capture: xe4\nPromotion: QQe1\nRegular move: e3e4')
        print('')
        move = input('Please enter your move: ')
        print('proceeding with action...')

        Chesspieces = chessboard.Scan() #Platzhalter

        vbc.useVBC(move, Chesspieces)

        print('Action done. Proceeding with next attempt...')
        print('####################################################################')