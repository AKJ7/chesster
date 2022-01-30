from chesster.vision_based_control.controller import VisualBasedController
from chesster.obj_recognition.chessboard_recognition import ChessBoard
from chesster.camera.realsense import RealSenseCamera
from chesster.Robot.UR10 import UR10Robot
from chesster.Schach_KI.class_chess_gameplay import ChessGameplay

if __name__ == "__main__":
    robot = UR10Robot()
    camera = RealSenseCamera()
    vbc = VisualBasedController(robot, "/")
    chessboard = ChessBoard()
    ChessAI = ChessGameplay(skill_level=5, threads=4, minimum_thinking_time=30, debug=False)
    i=0
    CheckMate=False
    print('####################################################################')
    print('Integration test 02: Integration of all three moduls (ChessAI, VBC, Object recognition')
    print('####################################################################')

    robotColor = input('please select the color of the robot/AI (b/w): ')

    if robotColor == "w":
        i=i+1
        humanColor = "b"
    else:
        humanColor = "w"

    while CheckMate == False:
        temp = input('press enter when your move is completed...')
        print('###################')
        print(f'Robot Action {i}')

        print('OBJ_R: Scanning Chessboard and calculating move done by player...')
        ChessPieces_New = chessboard.Scan() #Platzhalter
        print('OBJ_R: Scanning done.')

        print('CHESS_AI: Calculating best move...')
        moveHuman, _ = ChessAI.piece_notation_comparison(ChessPieces_Old, ChessPieces_New, humanColor)
        ChessAI.play_opponent(moveHuman)
        actions, _, CheckMate, _ = ChessAI.play_ki(ChessPieces_Old, humanColor)
        print('CHESS_AI: Best move calculated!')

        print('VBC: Proceeding to perform move by AI...')
        for move in actions:
            print('VBC: Doing subaction move: '+move)
            vbc.useVBC(move, ChessPieces)
        print('VBC: Move done!')
        print('')
        print('Its your turn again!')
        ChessPieces_Old = chessboard.Scan() #Platzhalter
        
    print('GAME OVER!')
        
