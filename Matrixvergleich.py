import chess
import chess.engine
import pandas as pd
from stockfish import Stockfish
stockfish = Stockfish("C:\\Users\\ywoda\\PycharmProjects\\Chesster\\chesster\\stockfish_14.1_win_x64_avx2.exe",
                      parameters={"Threads": 4, "Minimum Thinking Time":30, "Skill Level": 50})

before=[[1,1,1,1,1,1,1,1],[1,1,1,1,1,1,1,1],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[1,1,1,1,1,1,1,1],[1,1,1,1,1,1,1,1]]
after=[[1,1,1,1,1,1,1,1],[1,1,1,1,0,1,1,1],[0,0,0,0,0,0,0,0],[0,0,0,0,1,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[1,1,1,1,1,1,1,1],[1,1,1,1,1,1,1,1]]

def Matrixvergleich(before, after):
    Zug=pd.DataFrame(columns=['from','to'])
    alphabet=['a','b','c','d','e','f','g','h']
    for i in range(0,8):
        for j in range(0,8):
            #print(before[i][j])
            #print(after[i][j])
            if before[i][j] is not after[i][j]:
                print(i,j)
            if after[i][j] == 0 and before[i][j] == 1:
                iPrint= i + 1
                jPrint= alphabet[j]
                print('ausgehende Position ist ' +str(jPrint) + str(iPrint))
                Zugfrom = (str(jPrint) + str(iPrint))
                print(Zugfrom)
            if after[i][j] == 1 and before[i][j] == 0:
                iPrint = i + 1
                jPrint = alphabet[j]
                print('annehmende Position ist ' +str(jPrint) + str(iPrint))
                Zugto = (str(jPrint) + str(iPrint))
                print(Zugto)

    Zug.loc[0]=[Zugfrom,Zugto]
    print(Zug)
    ZugFinal=Zug['from'][0]+Zug['to'][0]
    print(ZugFinal)

    return ZugFinal

ermittelterZug=Matrixvergleich(before,after)

stockfish.set_fen_position("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
#bestmove=stockfish.get_best_move()
stockfish.make_moves_from_current_position([ermittelterZug])
print(stockfish.get_board_visual())