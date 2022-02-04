from chesster.vision_based_control.controller import VisualBasedController
from chesster.camera.realsense import RealSenseCamera
from chesster.Robot.UR10 import UR10Robot
from chesster.obj_recognition.object_recognition import ObjectRecognition
import cv2 as cv
if __name__ == "__main__":
    
    camera = RealSenseCamera()
    _ = camera.capture_color()
    _, _ = camera.capture_depth()
    detector = ObjectRecognition("C:/ChessterCalidata/Cali_0402-old.pkl")
    detector.start()
    chessPieces_Old = detector.get_chessboard_matrix()
    ScalingWidth = detector.board.scaling_factor_width
    ScalingHeight = detector.board.scaling_factor_height
    robot = UR10Robot()
    vbc = VisualBasedController(robot, "/")
    vbc.start() 
    i=0
    move = ""
    print('####################################################################')
    print('Integration test 01: Integration of Object/Chessboard recognition')
    print('and Vision-Based-Control')
    print('####################################################################')
    if detector.board.total_detected_fields() == 64:
        while True:
            i=i+1
            print(f'Attempt {i}')
            print(f'## Move Examples ##')
            print(f'Capture: xe4/nPromotion: QQe1/nRegular move: e3e4')
            print('')
            move = input('Please enter your move: ')
            print('proceeding with action...')
            d_img, _ = camera.capture_depth()
            c_img = camera.capture_color()
            if "x" in move:
                Chesspieces = [detector.get_chesspiece_info(move[2:], d_img), None] #Platzhalter
            elif "P" in move:
                Chesspieces = [None, detector.return_field(move[2:])] #Platzhalter
            else:
                Chesspieces = [detector.get_chesspiece_info(move[0:2], d_img), detector.return_field(move[2:])] #Platzhalter
            
            #detector.return_field(move[2:]).draw_roi(c_img, [0, 0, 255], 2)
            

            #cv.imshow("COLOR", c_img)
            vbc.useVBC(move, Chesspieces, d_img, [ScalingHeight, ScalingWidth])

            print('Action done. Proceeding with next attempt...')
            print('####################################################################')
    else:
        print('Calibration failed. Not 64 Fields detected.')