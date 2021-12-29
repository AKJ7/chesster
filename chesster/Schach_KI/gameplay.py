import chess
import chess.engine
import pandas as pd
from chesster.Schach_KI.Mirroring import *
from chesster.Schach_KI.comparison import *
from stockfish import Stockfish
stockfish = Stockfish("C:\\Users\\ywoda\\PycharmProjects\\Chesster\\chesster\\stockfish_14.1_win_x64_avx2.exe",
                      parameters={"Threads": 4, "Minimum Thinking Time":30, "Skill Level": 20})
#Set Initial game position by player color
def start_game(player_color):
    if player_color == 'w':
        #print('Cannot display game at the moment')
        stockfish.set_fen_position("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        #GegnerTurn = 'Spieler an der Reihe'
        print(stockfish.get_board_visual())
        Movecmd = []
        #mirrored Game necessary
    if player_color == 'b':
        # Schachfigurpositionen #Turn w/b #Rochade #en passent #gespielte Halbzüge seit letztem Bauernzug oder Figurschlag #Nummer nächster Zug (Schwarz: Start bei 1)
        stockfish.set_fen_position("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        #bestmove=stockfish.get_best_move()
        #stockfish.make_moves_from_current_position([bestmove])
        #GegnerTurn='Spieler an der Reihe'
        bestmove = stockfish.get_best_move()
        stockfish.make_moves_from_current_position([bestmove])
        Movecmd = [bestmove]
        print(stockfish.get_board_visual())
        #optionalVisualOutput here
    return Movecmd

#Function to roll back moves if incorrect
def rollback(Moves):
    Move1=Moves[0]
    RbMove1=Move1[2:4]+Move1[0:2]
    rollbackmove = [RbMove1]
    if len(Moves)==2:
        Move2=Moves[1]
        RbMove2 = Move2[2:4] + Move2[0:2]
        rollbackmove = [RbMove2,RbMove1]
    return rollbackmove
#Check for x of any chess piece
def proofKIFigurschlag(before,bestmove):
    x=int(ord(bestmove[2:3])-97)
    print(x)
    y=int(bestmove[3:4])-1
    print(y)
    proof = False
    #for i in range(0, 8):
        #for j in range(0, 8):
    if before[y][x] != 0:
        print(bestmove[2:4])
        print(before[y][x])
        proof=True
    return proof
#Check for En-Passent by KI and add secondmove for VBC
def KIenpassent(bestmove):
    list=[]
    position=stockfish.get_fen_position()
    for i, n in enumerate(position):
        #print(i, n)
        if n == " ":
            print(i)
            list.append(i)
    enpass = position[list[2]+1:list[2]+3] #get en passent out of fen position (index from space 3)

    print(list)
    print(enpass)
    #ybef=int(bestmove[1:2])-1
    #x=int(ord(bestmove[2:3])-97)
    #print(x)
    #y=int(bestmove[3:4])-1
    #print(y)
    proof = False
    secondmove =""
    if bestmove[2:4] == enpass:
        secondmove = bestmove[2:3] + bestmove[1:2] + "xx"
        proof = True
    #if before[y+1][x] != 0:
        #print(bestmove[2:4])
        #print(before[y+1][x])

    return proof, secondmove
#Check for Rochade by KI and add secondmove for VBC
def proofKIRochade(bestmove):
    secondmove = ""
    if bestmove == "e1g1":
        secondmove = "h1f1"
        proof=True
    else:
        if bestmove == "e1c1":
            secondmove = "a1d1"
            proof = True
        else:
            if bestmove == "e8g8":
                secondmove = "h8f8"
                proof = True
            else:
                if bestmove == "e8c8":
                    secondmove = "a8d8"
                    proof = True
                else:
                    proof = False
    return proof, secondmove
#Check for Promotion by KI and return true/false and chosen piece
def proofKIBauernumwandlung(bestmove):
    if len(bestmove)==5:
        proof=True
        if bestmove[4:5] == 'Q':
            Figur = 'Q'
        if bestmove[4:5] == 'q':
            Figur = 'q'
        if bestmove[4:5] == 'N':
            Figur = 'N'
        if bestmove[4:5] == 'n':
            Figur = 'n'
    else:
        proof=False
        Figur=""
    return proof, Figur
#Check for Status "White is in Chess"
def WhiteInChess():
    Evaluation = stockfish.get_evaluation()
    if Evaluation['type']=='mate' and Evaluation['value'] > 0:
        proof = True
    else:
        proof = False
    return proof
#Check for Status "Black is in Chess"
def BlackInChess():
    Evaluation = stockfish.get_evaluation()
    if Evaluation['type']=='mate' and Evaluation['value'] < 0:
        proof = True
    else:
        proof = False
    return proof
#Check for Status "is Checkmate"
def IsCheckMate(bestmove):
    if bestmove is None:
        proof=True
    else:
        proof=False
    return proof
#GetMatrixOutOfFenPosition
def BeforeForTests(fenposition):
    computebefore = str(fenposition)
    computebefore = computebefore.replace(str(8), "00000000")
    computebefore = computebefore.replace(str(7), "0000000")
    computebefore = computebefore.replace(str(6), "000000")
    computebefore = computebefore.replace(str(5), "00000")
    computebefore = computebefore.replace(str(4), "0000")
    computebefore = computebefore.replace(str(3), "000")
    computebefore = computebefore.replace(str(2), "00")
    computebefore = computebefore.replace(str(1), "0")
    computebefore = computebefore.replace("/", "")
    computebefore64 = computebefore[0:64]
    list = [[0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0]]
    list2 = [[0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0]]
    for i in range(len(computebefore64)):
        maindiv = int((i) / 8)
        rest = int((i) % 8)
        # print(type(computebefore64[i]))
        if computebefore64[i] == '0':
            list[maindiv][rest] = 0
        else:
            list[maindiv][rest] = computebefore64[i]
    count=7
    for n in range(0,8):
        list2[n]=list[count]
        count = count-1
    print(list2)
    return list2
#Gameplay with all proofs implemented
def gameplay(Move,Figurschlag,before,playercolor):
    IsInChessKI = False
    IsCheckmateKI = False
    IsInChessPlayer = False
    IsCheckmatePlayer = False
    if playercolor == 'w':
        Move = MirrorIfPlayerIsWhite(Move)
        #print(Move)
    proof=stockfish.is_move_correct(Move[0])
    if proof == True:
        stockfish.make_moves_from_current_position(Move)
        print(stockfish.get_board_visual())
        print(stockfish.get_evaluation())
        print(stockfish.get_fen_position())
        IsInChessKI = WhiteInChess()

        before=BeforeForTests(stockfish.get_fen_position())
        bestmove=stockfish.get_best_move()
        IsCheckmateKI = IsCheckMate(bestmove)
        stockfish.make_moves_from_current_position([bestmove])
        Movecmd = [bestmove]
        print(stockfish.get_evaluation())
        print(stockfish.get_fen_position())
        IsInChessPlayer = BlackInChess()
        bestmoveopponent = stockfish.get_best_move()
        IsCheckmatePlayer = IsCheckMate(bestmoveopponent)
        print(stockfish.get_board_visual())
        if proofKIFigurschlag(before,bestmove)==True:
            print("A chess piece has been captured by KI")
            Movecmd = [bestmove[2:4]+"xx",bestmove]
        proofKIEnpass,secondmove = KIenpassent(bestmove)
        if proofKIEnpass == True:
            print("En-passent is being performed by KI")
            Movecmd = [bestmove, secondmove]
        proofKIRoch, secondmove = proofKIRochade(bestmove)
        if proofKIRoch==True:
            print("Rochade is being performed by KI")
            Movecmd = [bestmove,secondmove]
        proofBauernumw, UmwFigur = proofKIBauernumwandlung(bestmove)
        if proofBauernumw==True:
            print("Protomtion to " + UmwFigur + " is being performed by KI")
            if UmwFigur == 'Q':
                Movecmd = [bestmove[0:4],bestmove[2:4] + "xx", "QQ" + bestmove[2:4]]
                if playercolor == 'w':
                    Movecmd.replace("QQ","qq")
            if UmwFigur == 'q':
                Movecmd = [bestmove[0:4],bestmove[2:4] + "xx", "qq" + bestmove[2:4]]
                if playercolor == 'w':
                    Movecmd.replace("qq","QQ")
            if UmwFigur == 'N':
                Movecmd = [bestmove[0:4], bestmove[2:4] + "xx", "NN" + bestmove[2:4]]
                if playercolor == 'w':
                    Movecmd.replace("NN","nn")
            if UmwFigur == 'n':
                Movecmd = [bestmove[0:4],bestmove[2:4] + "xx", "nn" + bestmove[2:4]]
                if playercolor == 'w':
                    Movecmd.replace("nn","NN")
        if playercolor == 'w':
            Movecmd = MirrorIfPlayerIsWhite(Movecmd)
        else:
            Movecmd=Movecmd
        print(Movecmd)
    else:
        print("Move incorrect - Roboter is reseting to default position")
        Rollback = rollback(Move)
        if playercolor == 'w':
            Movecmd = MirrorIfPlayerIsWhite(Rollback)
        else:
            Movecmd=Rollback
        print(Movecmd)

    return Movecmd,proof,IsInChessKI, IsInChessPlayer, IsCheckmateKI, IsCheckmatePlayer

