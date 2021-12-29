import chess
import chess.engine
import pandas as pd
from chesster.Schach_KI.comparison import *
from chesster.Schach_KI.gameplay import *

#[Zeile1],[Zeile2] etc. aus Robotersicht betrachtet !
beforeSchlag=[['W','W','W','W','W','W','W','W'],
        ['W','W','W','W','W','W','W','W'],
        [0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0],
        ['B',0,0,0,0,0,0,0],
        [0,'B','B','B','B','B','B','B'],
        ['B','B','B','B','B','B','B','B']]
afterSchlag=[['W','W','W','W','W','W','W','W'],
       ['W','W','W','W',0,'W','W','W'],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       ['W',0,0,0,0,0,0,0],
       [0,'B','B','B','B','B','B','B'],
       ['B','B','B','B','B','B','B','B']]
#lange weiße Rochade
beforeLW=[['W',0,0,0,'W','W','W','W'],
       ['W','W','W','W','W','W','W','W'],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       ['B','B','B','B','B','B','B','B'],
       ['B','B','B','B','B','B','B','B']]
afterLW=[[0,0,'W','W',0,'W','W','W'],
       ['W','W','W','W','W','W','W','W'],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       ['B','B','B','B','B','B','B','B'],
       ['B','B','B','B','B','B','B','B']]
#kurze weiße Rochade
beforeKW=[['W','W','W','W','W',0,0,'W'],
       ['W','W','W','W','W','W','W','W'],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       ['B','B','B','B','B','B','B','B'],
       ['B','B','B','B','B','B','B','B']]
afterKW=[['W','W','W','W',0,'W','W',0],
       ['W','W','W','W','W','W','W','W'],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       ['B','B','B','B','B','B','B','B'],
       ['B','B','B','B','B','B','B','B']]
#lange schwarze Rochade
beforeLS=[['W','W','W','W','W','W','W','W'],
       ['W','W','W','W','W','W','W','W'],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       ['B','B','B','B','B','B','B','B'],
       ['B',0,0,0,'B','B','B','B']]
afterLS=[['W','W','W','W','W','W','W','W'],
       ['W','W','W','W','W','W','W','W'],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       ['B','B','B','B','B','B','B','B'],
       [0,0,'B','B',0,'B','B','B']]
#kurze schwarze Rochade
beforeKS=[['W','W','W','W','W','W','W','W'],
       ['W','W','W','W','W','W','W','W'],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       ['B','B','B','B','B','B','B','B'],
       ['B','B','B','B','B',0,0,'B']]
afterKS=[['W','W','W','W','W','W','W','W'],
       ['W','W','W','W','W','W','W','W'],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       ['B','B','B','B','B','B','B','B'],
       ['B','B','B','B',0,'B','B',0]]
############################################With detail informaton########
#[Zeile1],[Zeile2] etc. aus Robotersicht betrachtet !
beforeHit=[['R','N','B','Q','K','B',0,'R'],
           ['P','P','P',0,'P','P','P','P'],
           [0,0,0,0,0,'N',0,0],
           [0,0,0,'P','p',0,0,0],
           [0,0,0,0,0,0,0,0],
           [0,0,0,0,0,0,0,0],
           ['p','p','p','p',0,'p','p','p'],
           ['r','n','b','q','k','b','n','r']]
afterHit=[['R','N','B','Q','K','B',0,'R'],
       ['P','P','P',0,'P','P','P','P'],
       [0,0,0,'p',0,'N',0,0],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       ['p','p','p','p',0,'p','p','p'],
       ['r','n','b','q','k','b','n','r']]
#lange weiße Rochade
beforeLW=[['R',0,0,0,'K','B','N','R'],
       ['P','P','P','P','P','P','P','P'],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       ['p','p','p','p','p','p','p','p'],
       ['r','n','b','q','k','b','n','r']]
afterLW=[[0,0,'K','R',0,'B','N','R'],
       ['P','P','P','P','P','P','P','P'],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       ['p','p','p','p','p','p','p','p'],
       ['r','n','b','q','k','b','n','r']]
#kurze weiße Rochade
beforeKW=[['R','N','B','Q','K',0,0,'R'],
       ['P','P','P','P','P','P','P','P'],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       ['p','p','p','p','p','p','p','p'],
       ['r','n','b','q','k','b','n','r']]
afterKW=[['R','N','B','Q',0,'R','K',0],
       ['P','P','P','P','P','P','P','P'],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       ['p','p','p','p','p','p','p','p'],
       ['r','n','b','q','k','b','n','r']]
#lange schwarze Rochade
beforeLS=[['R','N','B','Q','K','B','N','R'],
       ['P','P','P','P','P','P','P','P'],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       ['p','p','p','p','p','p','p','p'],
       ['r',0,0,0,'k','b','n','r']]
afterLS=[['R','N','B','Q','K','B','N','R'],
       ['P','P','P','P','P','P','P','P'],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       ['p','p','p','p','p','p','p','p'],
       [0,0,'k','r',0,'b','n','r']]
#kurze schwarze Rochade
beforeKS=[['R','N','B','Q','K','B','N','R'],
       ['P','P','P','P','P','P','P','P'],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       ['p','p','p','p','p','p','p','p'],
       ['r','n','b','q','k',0,0,'r']]
afterKS=[['R','N','B','Q','K','B','N','R'],
       ['P','P','P','P','P','P','P','P'],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       [0,0,0,0,0,0,0,0],
       ['p','p','p','p','p','p','p','p'],
       ['r','n','b','q',0,'r','k',0]]

#FullMatrixComp(beforeKS,afterKS,player_color)
#FullMatrixComp(beforeKW,afterKW)
#FullMatrixComp(beforeLS,afterLS)
#FullMatrixComp(beforeLW,afterLW)
player_color='b'
move,Hitting=FullMatrixComp(beforeKS,afterKS,player_color)
print(move)
move,Hit=FullMatrixComp(beforeHit,afterHit,player_color)
print(move)
#beforeHit=[['R','N','B','Q','K','B','N','R'],
       #['P','P','P','P','P','P','P','P'],
       #[0,0,0,0,0,0,0,0],
       #[0,0,0,0,0,0,0,0],
       #[0,0,0,0,0,0,0,0],
       #[0,0,0,0,0,0,0,0],
       #['p','p','p','p','p','p','p','p'],
       #['r','n','b','q','k','b','n','r']]
stockfish.set_fen_position("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
print(stockfish.get_board_visual())
stockfish.make_moves_from_current_position(['f2f4','g8h6','f4f5'])
stockfish.make_moves_from_current_position(['f2f4','g8h6','f4f5'])
print(stockfish.get_board_visual())
print(stockfish.get_fen_position())
#stockfish.make_moves_from_current_position(['h7h5','f2f4'])
#print(stockfish.get_board_visual())
#print(stockfish.get_fen_position())
move=["e7e5"]
cmd=gameplay(move,False,afterHit,player_color)
print(cmd)

print(stockfish.get_evaluation())
computebefore = str(stockfish.get_fen_position())
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




#[hallo],string=start_game('w')
#print([hallo])
#print(string)