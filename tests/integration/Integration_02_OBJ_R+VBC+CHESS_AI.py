from chesster.vision_based_control.controller import VisualBasedController
from chesster.obj_recognition import *
from chesster.camera.realsense import RealSenseCamera
from chesster.Robot.UR10 import UR10Robot
from chesster.Schach_KI.class_chess_gameplay import ChessGameplay

if __name__ == "__main__":
    robot = UR10Robot()
    camera = RealSenseCamera()
    vbc = VisualBasedController(robot, "/")
    detector = ObjectRecognition()
    detector.start()
    chessPieces_Old = detector.get_chesspiece_info() 
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
    
    while CheckMate == False:
        if i==0 and robotColor=="w":
            print('###################')
            print(f'Robot Action {i}')
            print('Robot starts the game.')
            print('CHESS_AI: Calculating best move...')
            actions, _, CheckMate, _ = ChessAI.play_ki(ChessPieces_Old, humanColor)
            print('CHESS_AI: Best move calculated!')
        else:
            temp = input('press enter when your move is completed...')
            print('###################')
            print(f'Robot Action {i}')

            print('OBJ_R: Scanning Chessboard and calculating move done by player...')
            detector.determine_changes()
            chessPieces_New = detector.get_chesspiece_info()
            print('OBJ_R: Scanning done.')

            print('CHESS_AI: Calculating best move...')
            moveHuman, _ = ChessAI.piece_notation_comparison(chessPieces_Old, chessPieces_New, humanColor)
            ChessAI.play_opponent(moveHuman) --> TBD
            actions, _, CheckMate, _ = ChessAI.play_ki(ChessPieces_Old, humanColor)
            print('CHESS_AI: Best move calculated!')

        print('VBC: Proceeding to perform move by AI...')
        for move in actions:
            print('VBC: Doing subaction move: '+move)
            vbc.useVBC(move, ChessPieces)
        print('VBC: Move done!')
        print('')
        detector.determine_changes()
        ChessPieces_Old = detector.get_chesspiece_info() #Platzhalter
        print('Its your turn again!')
        i=i+1
        
    print('GAME OVER!')
        
