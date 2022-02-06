from numpy import object_
from chesster.vision_based_control.controller import VisualBasedController
from chesster.obj_recognition.object_recognition import ObjectRecognition 
from chesster.camera.realsense import RealSenseCamera
from chesster.Robot.UR10 import UR10Robot
from chesster.Schach_KI.class_chess_gameplay import ChessGameplay
import cv2 as cv
if __name__ == "__main__":
    robot = UR10Robot()
    robot.start()
    camera = RealSenseCamera()
    _ = camera.capture_color()
    _, _ = camera.capture_depth()
    vbc = VisualBasedController(robot, "/")
    vbc.start()
    detector = ObjectRecognition("C:/ChessterCalidata/Cali_0402-old.pkl")
    detector.start()
    ScalingWidth = detector.board.scaling_factor_width
    ScalingHeight = detector.board.scaling_factor_height
    chessPieces_Old = detector.get_chessboard_matrix()
    ChessAI = ChessGameplay(skill_level=5, threads=4, minimum_thinking_time=30, debug=False)
    i=0
    CheckMate=False
    print('####################################################################')
    print('Integration test 02: Integration of all three moduls (ChessAI, VBC, Object recognition')
    print('####################################################################')

    robotColor = input('please select the color of the robot/AI (b/w): ')

    if robotColor == "w":
        humanColor = "b"
        robot.StartGesture(Beginner=True)
    else:
        humanColor = "w"
        robot.StartGesture(Beginner=False)
    
    print('Taking a picture of the base layout...')
    current_cimg = camera.capture_color()
    current_dimg, _ = camera.capture_depth()

    while CheckMate == False:
        if i==0 and robotColor=="w":
            print('###################')
            print(f'Robot Action {i}')
            print('Robot starts the game.')
            print('CHESS_AI: Calculating best move...')
            actions, _, CheckMate, _ = ChessAI.play_ki(chessPieces_Old, humanColor)
            print('CHESS_AI: Best move calculated!')
        else:
            if i==0:
                print('You start! Make your first move.')
            else:
                print('your turn again. ')
            temp = input('press enter when your move is completed...')
            print('###################')
            print(f'Robot Action {i}')

            print('Taking pictures...')
            previous_cimg = current_cimg
            previous_dimg = current_dimg
            current_cimg = camera.capture_color()
            current_dimg, _ = camera.capture_depth()
            print('OBJ_R: Scanning Chessboard and calculating move done by player...')
            chessPieces_Old = chessPieces_New
            if robotColor=="w":
                current_player_color = "b"
            else:
                current_player_color = "w"
            chessPieces_New, moveHuman = detector.determine_changes(previous_cimg, current_cimg, current_player_color)
            print('OBJ_R: Scanning done.')

            print('CHESS_AI: Calculating best move...')
            print(chessPieces_Old)
            print(chessPieces_New)
            #moveHuman, _ = ChessAI.piece_notation_comparison(chessPieces_Old, chessPieces_New, humanColor)
            _, Proof,_, CheckMate = ChessAI.play_opponent([moveHuman], humanColor)
            if Proof == False:
                break
            chessPieces_Old = chessPieces_New
            actions, _, CheckMate, _ = ChessAI.play_ki(chessPieces_Old, humanColor)
            print('CHESS_AI: Best move calculated!')

        print('VBC: Proceeding to perform move by AI...')
        for i, move in enumerate(actions):
            if "x" in move:
                Chesspieces = [detector.get_chesspiece_info(move[0:2], current_dimg), None] #Platzhalter
            elif "P" in move:
                Chesspieces = [None, detector.return_field(move[2:])] #Platzhalter
            else:
                Chesspieces = [detector.get_chesspiece_info(move[0:2], current_dimg), detector.return_field(move[2:])] #Platzhalter
            print('VBC: Doing subaction move: '+move)
            if i == len(actions)-1:
                print('Last move of given action -> Homing after move')
                lastMove = True
            else:
                lastMove = False
            vbc.useVBC(move, Chesspieces, current_dimg, [ScalingHeight, ScalingWidth], lastMove)
        print('VBC: Move done!')
        print('')
        
        print('Taking picture of current chessboard layout..')
        previous_cimg = current_cimg.copy()
        previous_dimg = current_dimg.copy()
        current_cimg = camera.capture_color()
        current_dimg, _ = camera.capture_depth()
        if robotColor=="w":
            current_player_color = "w"
        else:
            current_player_color = "b"
        chessPieces_New, moveAI = detector.determine_changes(previous_cimg, current_cimg, current_player_color) #flipped! Because new=old and old=new
        print(chessPieces_Old)
        print(chessPieces_New)
        print('###################')
        print(f'Robot move {i} done.')
        print('###################')
        i=i+1
        
    print('GAME OVER!')
        
