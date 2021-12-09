import chess
import chess.engine
import pandas as pd
#from stockfish import Stockfish
#stockfish = Stockfish("C:\\Users\\ywoda\\PycharmProjects\\Chesster\\chesster\\stockfish_14.1_win_x64_avx2.exe",
                      #parameters={"Threads": 4, "Minimum Thinking Time":30, "Skill Level": 50})

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

def Matrixvergleich(before, after):
    Zug=pd.DataFrame(columns=['from','to'])
    ZugFinal=[]
    alphabet=['a','b','c','d','e','f','g','h']
    #zahlen=[8,7,6,5,4,3,2,1]
    Zugfrom=pd.DataFrame(columns=['from'])
    Zugto=pd.DataFrame(columns=['to'])
    countFrom=0
    countTo=0
    movementdetected=0
    colorchangedetected=0 #matrix with distinction in colors
    for i in range(0,8):
        for j in range(0,8):
            #print(before[i][j])
            #print(after[i][j])
            #if before[i][j] is not after[i][j]:
                #print(i,j)
#Check for MovementFromPosition
            if after[i][j] == 0 and (before[i][j] =='W' or before[i][j] =='B'):
                iPrint= i + 1
                jPrint= alphabet[j]
                print('ausgehende Position ist ' +str(jPrint) + str(iPrint))
                Zugfrom.loc[countFrom]  = (str(jPrint) + str(iPrint))
                countFrom = countFrom + 1
                print(Zugfrom)
                movementdetected = movementdetected + 1
                print('Changes: ' + str(movementdetected+colorchangedetected))
#Check for MovementToPosition
            if before[i][j] == 0 and (after[i][j] =='W' or after[i][j] =='B'):
                iPrint = i + 1
                jPrint = alphabet[j]
                print('annehmende Position ist ' +str(jPrint) + str(iPrint))
                Zugto.loc[countTo] = (str(jPrint) + str(iPrint))
                countTo = countTo + 1
                print(Zugto)
                movementdetected = movementdetected + 1
                print('Changes: ' + str(movementdetected+colorchangedetected))
#Check for ColorChange
            if (after[i][j] == 'W' and before[i][j] =='B') or (after[i][j] == 'B' and before[i][j] =='W'):
                iPrint = i + 1
                jPrint = alphabet[j]
                print('annehmende Position ist ' + str(jPrint) + str(iPrint))
                Zugto.loc[countTo] = (str(jPrint) + str(iPrint))
                countTo = countTo + 1
                print(Zugto)
                colorchangedetected = colorchangedetected + 1
                print('Changes: ' + str(movementdetected+colorchangedetected))
# lange weiße Rochade
        if i == 0: #lange weiße Rochade
            if type(before[0][4]) == str and type(after[0][2]) == str and type(before[0][0]) == str and type(after[0][3]) == str\
                    and before[0][1] == 0 and before[0][2] == 0 and before[0][3] == 0\
                    and after[0][0] == 0 and after[0][1] == 0 and after[0][4] == 0:
                ZugFinal.extend(['e1c1','a1d1'])
                print('Lange weiße Rochade')
# kurze weiße Rochade
        if i == 0: #kurze weiße Rochade
            if type(before[0][4]) == str and type(after[0][5]) == str\
                    and type(before[0][7]) == str and type(after[0][6]) == str\
                    and before[0][5] == 0 and before[0][6] == 0 and after[0][4] == 0 and after[0][7] == 0:
                ZugFinal.extend(['e1g1','h1f1'])
                print('Kurze weiße Rochade')
# lange schwarze Rochade
        if i == 7: #lange schwarze Rochade
            if type(before[7][4]) == str and type(after[7][2]) == str and type(before[7][0]) == str and type(after[7][3]) == str and \
                    before[7][1] == 0 and before[7][2] == 0 and before[7][3] == 0 and \
                    after[7][0] == 0 and after[7][1] == 0 and after[7][4] == 0:
                ZugFinal.extend(['e8c8', 'a8d8'])
                print('Lange schwarze Rochade')
# kurze schwarze Rochade
        if i == 7: #kurze schwarze Rochade
            if type(before[7][4]) == str and type(after[7][5]) == str\
                    and type(before[7][7]) == str and type(after[7][6]) == str \
                    and before[7][5] == 0 and before[7][6] == 0 and after[7][4] == 0 and after[7][7] == 0:
                ZugFinal.extend(['e8g8', 'h8f8'])
                print('Kurze schwarze Rochade')

    if movementdetected + colorchangedetected == 2:
        Zug.loc[0]=[Zugfrom['from'][0],Zugto['to'][0]]
        ZugFinal = Zug['from'][0] + Zug['to'][0]
    if movementdetected + colorchangedetected <2:
        print(Zug)
        ZugFinal = 0
    if movementdetected + colorchangedetected > 2:
        Zug.loc[0] = [Zugfrom['from'][0], Zugto['to'][0]]
        Zug.loc[1] = [Zugfrom['from'][1],Zugto['to'][1]]
        #ZugFinal = 'No clear move without extra if-clause'
    if colorchangedetected > 0:
        Figurschlag = True
    else:
        Figurschlag = False
    print(Zug)

    return ZugFinal, Figurschlag

#Figurschlag: *Schlag
#Rochaden: lang:L, kurz: K, weiß: W, schwarz:S
ermittelterZug,Schlag=Matrixvergleich(beforeLW,afterLW)
print(ermittelterZug)
print(Schlag)
#stockfish.set_fen_position("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
#bestmove=stockfish.get_best_move()
#stockfish.make_moves_from_current_position([ermittelterZug])
#print(stockfish.get_board_visual())

import chess
import chess.engine
import pandas as pd
#from stockfish import Stockfish
#stockfish = Stockfish("C:\\Users\\ywoda\\PycharmProjects\\Chesster\\chesster\\stockfish_14.1_win_x64_avx2.exe",
                      #parameters={"Threads": 4, "Minimum Thinking Time":30, "Skill Level": 50})

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

def FullMatrixComp(before, after):
    Zug=pd.DataFrame(columns=['from','to'])
    ZugFinal=[]
    alphabet=['a','b','c','d','e','f','g','h']
    #zahlen=[8,7,6,5,4,3,2,1]
    Zugfrom=pd.DataFrame(columns=['from'])
    Zugto=pd.DataFrame(columns=['to'])
    countFrom=0
    countTo=0
    movementdetected=0
    colorchangedetected=0 #matrix with distinction in colors
    for i in range(0,8):
        for j in range(0,8):
            #print(before[i][j])
            #print(after[i][j])
            #if before[i][j] is not after[i][j]:
                #print(i,j)
#Check for MovementFromPosition
            if after[i][j] == 0 and (type(before[i][j]) == str) :
                iPrint= i + 1
                jPrint= alphabet[j]
                print('ausgehende Position ist ' +str(jPrint) + str(iPrint))
                Zugfrom.loc[countFrom]  = (str(jPrint) + str(iPrint))
                countFrom = countFrom + 1
                print(Zugfrom)
                movementdetected = movementdetected + 1
                print('Changes: ' + str(movementdetected+colorchangedetected))
#Check for MovementToPosition
            if before[i][j] == 0 and (type(after[i][j]) ==str):
                iPrint = i + 1
                jPrint = alphabet[j]
                print('annehmende Position ist ' +str(jPrint) + str(iPrint))
                Zugto.loc[countTo] = (str(jPrint) + str(iPrint))
                countTo = countTo + 1
                print(Zugto)
                movementdetected = movementdetected + 1
                print('Changes: ' + str(movementdetected+colorchangedetected))
#Check for ColorChange
            if not type(after[i][j])==int and not type(before[i][j])==int:
                if (str.isupper(after[i][j]) and str.islower(before[i][j])) or (str.islower(after[i][j]) and str.isupper(before[i][j])):
                    iPrint = i + 1
                    jPrint = alphabet[j]
                    print('annehmende Position ist ' + str(jPrint) + str(iPrint))
                    Zugto.loc[countTo] = (str(jPrint) + str(iPrint))
                    countTo = countTo + 1
                    print(Zugto)
                    colorchangedetected = colorchangedetected + 1
                    print('Changes: ' + str(movementdetected+colorchangedetected))
# lange weiße Rochade
        if i == 0: #lange weiße Rochade
            if before[0][4] == 'K' and after[0][2] == 'K' and before[0][0] == 'R'and after[0][3] == 'R':#\
                    #and before[0][1] == 0 and before[0][2] == 0 and before[0][3] == 0\
                    #and after[0][0] == 0 and after[0][1] == 0 and after[0][4] == 0:
                ZugFinal.extend(['e1c1','a1d1'])
                print('Lange weiße Rochade')
# kurze weiße Rochade
        if i == 0: #kurze weiße Rochade
            if before[0][4] == 'K' and after[0][5] == 'K'\
                    and before[0][7] == 'R' and after[0][6] == 'R':#\
                    #and before[0][5] == 0 and before[0][6] == 0 and after[0][4] == 0 and after[0][7] == 0:
                ZugFinal.extend(['e1g1','h1f1'])
                print('Kurze weiße Rochade')
# lange schwarze Rochade
        if i == 7: #lange schwarze Rochade
            if before[7][4] == 'k' and after[7][2] == 'k' and before[7][0] == 'r' and after[7][3] == 'r':# and #\
                    #before[7][1] == 0 and before[7][2] == 0 and before[7][3] == 0 and \
                    #after[7][0] == 0 and after[7][1] == 0 and after[7][4] == 0:
                ZugFinal.extend(['e8c8', 'a8d8'])
                print('Lange schwarze Rochade')
# kurze schwarze Rochade
        if i == 7: #kurze schwarze Rochade
            if before[7][4] == 'k' and after[7][5] == 'k'\
                    and before[7][7] == 'r' and after[7][6] == 'r':#\
                    #and before[7][5] == 0 and before[7][6] == 0 and after[7][4] == 0 and after[7][7] == 0:
                ZugFinal.extend(['e8g8', 'h8f8'])
                print('Kurze schwarze Rochade')

    if movementdetected + colorchangedetected == 2:
        Zug.loc[0]=[Zugfrom['from'][0],Zugto['to'][0]]
        ZugFinal = Zug['from'][0] + Zug['to'][0]
    if movementdetected + colorchangedetected <2:
        print(Zug)
        ZugFinal = 0
    if movementdetected + colorchangedetected > 2:
        Zug.loc[0] = [Zugfrom['from'][0], Zugto['to'][0]]
        Zug.loc[1] = [Zugfrom['from'][1],Zugto['to'][1]]
        #ZugFinal = 'No clear move without extra if-clause'
    if colorchangedetected > 0:
        Figurschlag = True
    else:
        Figurschlag = False
    print(Zug)

    return ZugFinal, Figurschlag

#Figurschlag: *Schlag
#Rochaden: lang:L, kurz: K, weiß: W, schwarz:S
newZug,Hit=FullMatrixComp(beforeLW,afterLW)
print(newZug)
print(Hit)
#stockfish.set_fen_position("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
#bestmove=stockfish.get_best_move()
#stockfish.make_moves_from_current_position([ermittelterZug])
#print(stockfish.get_board_visual())