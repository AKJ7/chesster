import chess
import chess.engine
import pandas as pd
from stockfish import Stockfish
stockfish = Stockfish("C:\\Users\\ywoda\\PycharmProjects\\Chesster\\chesster\\stockfish_14.1_win_x64_avx2.exe",
                      parameters={"Threads": 4, "Minimum Thinking Time":30, "Skill Level": 50})

def start_game(player_color):
    if player_color == 'w':
        print('Cannot display game at the moment')
        #mirrored Game necessary
    if player_color == 'b':
        # Schachfigurpositionen #Turn w/b #Rochade #en passent #gespielte Halbzüge seit letztem Bauernzug oder Figurschlag #Nummer nächster Zug (Schwarz: Start bei 1)
        stockfish.set_fen_position("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        bestmove=stockfish.get_best_move()
        stockfish.make_moves_from_current_position([bestmove])
        GegnerTurn='Spieler an der Reihe'
        #optionalVisualOutput here
    return [bestmove], GegnerTurn

[hallo],string=start_game('b')
print([hallo])
print(string)

Evaluation=stockfish.get_evaluation()
print(Evaluation)
Evaluation['type']='mate'
print(Evaluation)
def IsInMatebyB(Evaluation):
    if Evaluation['type']=='mate':
        proof = True
        Ausgabe = "We've got a Mate by black here"

    else:
        proof = False
        Ausgabe = "Nächster Spielzug"
    return proof, Ausgabe

print(IsInMatebyB(Evaluation))#####Test

def IsInMatebyW(Evaluation):
    if Evaluation['type']=='mate':
        proof = True
        Ausgabe = "We've got a Mate by white here"
    else:
        proof = False
        Ausgabe = "Nächster Spielzug"
    return proof, Ausgabe

def IsCheckmatebyB(bestmove):
    if bestmove is None:
        proof=True
        Ausgabe="We've got a CheckMate by black here"
    else:
        proof=False
    return proof, Ausgabe

def IsCheckmatebyW(bestmove):
    if bestmove is None:
        proof=True
        Ausgabe="We've got a CheckMate by white here"
    else:
        proof=False
    return proof, Ausgabe


def Matrixvergleich(before, after):
    for i in range(1,8):
        for j in range(1,8):
            if before[i,j] is not after [i,j]:
                print(i,j)

    return
before=[]
#for i in range(1,8):
    #for j in range(1,8):
        #if i == 1:
         #   before[i,j]=1
        #if i ==2:
        #    before[i,j]=2
        #if i == 7:
        #    before[i,j]=7
        #if i ==8:
        #    before[i,j]=8
#print(before)
before=[[1,1,1,1,1,1,1,1],[1,1,1,1,1,1,1,1],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0]]
after=[[1,1,1,1,1,1,1,1],[1,1,1,0,1,1,1,1],[0,0,0,1,0,0,0,0],[0,0,0,0,0,0,0,0]]


