from numpy import object_
from chesster.vision_based_control.controller import VisualBasedController
from chesster.obj_recognition.object_recognition import ObjectRecognition 
from chesster.camera.realsense import RealSenseCamera
from chesster.Robot.UR10 import UR10Robot
from chesster.Schach_KI.class_chess_gameplay import ChessGameplay

if __name__ == "__main__":
    robot = UR10Robot()
    camera = RealSenseCamera()
    _ = camera.capture_color()
    _, _ = camera.capture_depth()
    vbc = VisualBasedController(robot, "/")
    detector = ObjectRecognition("C:/Chesster/test.pkl")
    detector.start()
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
    else:
        humanColor = "w"
    
    print('Taking a picture of the base layout...')
    previous_cimg = camera.capture_color()
    previous_dimg, _ = camera.capture_depth()

    while CheckMate == False:
        if i==0 and robotColor=="w":
            print('###################')
            print(f'Robot Action {i}')
            print('Robot starts the game.')
            print('CHESS_AI: Calculating best move...')
            actions, _, CheckMate, _ = ChessAI.play_ki(ChessPieces_Old, humanColor)
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
            current_cimg = camera.capture_color()
            current_dimg, _ = camera.capture_depth()
            print('OBJ_R: Scanning Chessboard and calculating move done by player...')
            chessPieces_New = detector.determine_changes(previous_cimg, current_cimg)
            print('OBJ_R: Scanning done.')

            print('CHESS_AI: Calculating best move...')
            moveHuman, _ = ChessAI.piece_notation_comparison(chessPieces_Old, chessPieces_New, humanColor)
            ChessAI.play_opponent(moveHuman) --> TBD
            actions, _, CheckMate, _ = ChessAI.play_ki(ChessPieces_Old, humanColor)
            print('CHESS_AI: Best move calculated!')

        print('VBC: Proceeding to perform move by AI...')
        for move in actions:
            print('VBC: Doing subaction move: '+move)
            vbc.useVBC(move, [detector.get_chesspiece_info(move[2:4], current_dimg), detector.get_chesspiece_info(move[4:], current_dimg)], current_dimg)
        print('VBC: Move done!')
        print('')
        
        print('Taking picture of current chessboard layout..')
        previous_cimg = camera.capture_color()
        previous_dimg, _ = camera.capture_depth()
        ChessPieces_Old = detector.determine_changes(current_cimg, previous_cimg) #flipped! Because new=old and old=new
        print('###################')
        print(f'Robot move {i} done.')
        print('###################')
        i=i+1
        
    print('GAME OVER!')
        
