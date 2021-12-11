import chess
import chess.engine
import pandas as pd
#from stockfish import Stockfish
#stockfish = Stockfish("C:\\Users\\ywoda\\PycharmProjects\\Chesster\\chesster\\stockfish_14.1_win_x64_avx2.exe",
                      #parameters={"Threads": 4, "Minimum Thinking Time":30, "Skill Level": 50})

#[Zeile1],[Zeile2] etc. aus Robotersicht betrachtet !
def Matrixvergleich(before, after):
    Move=pd.DataFrame(columns=['from','to'])
    MoveFinal=[]
    alphabet=['a','b','c','d','e','f','g','h']
    #zahlen=[8,7,6,5,4,3,2,1]
    Movefrom=pd.DataFrame(columns=['from'])
    Moveto=pd.DataFrame(columns=['to'])
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
                Movefrom.loc[countFrom]  = (str(jPrint) + str(iPrint))
                countFrom = countFrom + 1
                print(Movefrom)
                movementdetected = movementdetected + 1
                print('Changes: ' + str(movementdetected+colorchangedetected))
#Check for MovementToPosition
            if before[i][j] == 0 and (after[i][j] =='W' or after[i][j] =='B'):
                iPrint = i + 1
                jPrint = alphabet[j]
                print('annehmende Position ist ' +str(jPrint) + str(iPrint))
                Moveto.loc[countTo] = (str(jPrint) + str(iPrint))
                countTo = countTo + 1
                print(Moveto)
                movementdetected = movementdetected + 1
                print('Changes: ' + str(movementdetected+colorchangedetected))
#Check for ColorChange
            if (after[i][j] == 'W' and before[i][j] =='B') or (after[i][j] == 'B' and before[i][j] =='W'):
                iPrint = i + 1
                jPrint = alphabet[j]
                print('annehmende Position ist ' + str(jPrint) + str(iPrint))
                Moveto.loc[countTo] = (str(jPrint) + str(iPrint))
                countTo = countTo + 1
                print(Moveto)
                colorchangedetected = colorchangedetected + 1
                print('Changes: ' + str(movementdetected+colorchangedetected))
# lange weiße Rochade
        if i == 0: #lange weiße Rochade
            if type(before[0][4]) == str and type(after[0][2]) == str and type(before[0][0]) == str and type(after[0][3]) == str\
                    and before[0][1] == 0 and before[0][2] == 0 and before[0][3] == 0\
                    and after[0][0] == 0 and after[0][1] == 0 and after[0][4] == 0:
                MoveFinal.extend(['e1c1','a1d1'])
                print('Lange weiße Rochade')
# kurze weiße Rochade
        if i == 0: #kurze weiße Rochade
            if type(before[0][4]) == str and type(after[0][5]) == str\
                    and type(before[0][7]) == str and type(after[0][6]) == str\
                    and before[0][5] == 0 and before[0][6] == 0 and after[0][4] == 0 and after[0][7] == 0:
                MoveFinal.extend(['e1g1','h1f1'])
                print('Kurze weiße Rochade')
# lange schwarze Rochade
        if i == 7: #lange schwarze Rochade
            if type(before[7][4]) == str and type(after[7][2]) == str and type(before[7][0]) == str and type(after[7][3]) == str and \
                    before[7][1] == 0 and before[7][2] == 0 and before[7][3] == 0 and \
                    after[7][0] == 0 and after[7][1] == 0 and after[7][4] == 0:
                MoveFinal.extend(['e8c8', 'a8d8'])
                print('Lange schwarze Rochade')
# kurze schwarze Rochade
        if i == 7: #kurze schwarze Rochade
            if type(before[7][4]) == str and type(after[7][5]) == str\
                    and type(before[7][7]) == str and type(after[7][6]) == str \
                    and before[7][5] == 0 and before[7][6] == 0 and after[7][4] == 0 and after[7][7] == 0:
                MoveFinal.extend(['e8g8', 'h8f8'])
                print('Kurze schwarze Rochade')

    if movementdetected + colorchangedetected == 2:
        Move.loc[0]=[Movefrom['from'][0],Moveto['to'][0]]
        MoveFinal = Move['from'][0] + Move['to'][0]
    if movementdetected + colorchangedetected <2:
        print(Move)
        MoveFinal = 0
    if movementdetected + colorchangedetected > 2:
        Move.loc[0] = [Movefrom['from'][0], Moveto['to'][0]]
        Move.loc[1] = [Movefrom['from'][1],Moveto['to'][1]]
        #MoveFinal = 'No clear move without extra if-clause'
    if colorchangedetected > 0:
        Figurschlag = True
    else:
        Figurschlag = False
    print(Move)

    return MoveFinal, Figurschlag

#[Zeile1],[Zeile2] etc. aus Robotersicht betrachtet !
def FullMatrixComp(before, after):
    Move=pd.DataFrame(columns=['from','to'])
    MoveFinal=[]
    alphabet=['a','b','c','d','e','f','g','h']
    #zahlen=[8,7,6,5,4,3,2,1]
    Movefrom=pd.DataFrame(columns=['from'])
    Moveto=pd.DataFrame(columns=['to'])
    countFrom=0
    countTo=0
    movementdetected=0
    colorchangedetected=0 #matrix with distinction in colors
    countNbefore=0
    countNafter = 0
    countnbefore=0
    countnafter=0
    countQbefore=0
    countQafter=0
    countqbefore = 0
    countqafter = 0
    for i in range(0,8):
        for j in range(0,8):
            #Bauernumwandlung
            if before[i][j] == 'Q':
                countQbefore=countQbefore + 1
            if after[i][j] == 'Q':
                countQafter=countQafter +1
            if before[i][j] == 'q':
                countqbefore = countqbefore + 1
            if after[i][j] == 'q':
                countqafter = countqafter + 1
            if before[i][j] == 'N':
                countNbefore=countNbefore + 1
            if after[i][j] == 'N':
                countNafter=countNafter +1
            if before[i][j] == 'n':
                countnbefore = countnbefore + 1
            if after[i][j] == 'n':
                countnafter = countnafter + 1
            #print(before[i][j])
            #print(after[i][j])
            #if before[i][j] is not after[i][j]:
                #print(i,j)
#Check for MovementFromPosition
            if after[i][j] == 0 and (type(before[i][j]) == str) :
                iPrint= i + 1
                jPrint= alphabet[j]
                print(str(before[i][j]) + ' von ' + str(jPrint) + str(iPrint))
                Movefrom.loc[countFrom]  = (str(jPrint) + str(iPrint))
                countFrom = countFrom + 1
                print(Movefrom)
                movementdetected = movementdetected + 1
                print('Changes: ' + str(movementdetected+colorchangedetected))
#Check for MovementToPosition
            if before[i][j] == 0 and (type(after[i][j]) ==str):
                iPrint = i + 1
                jPrint = alphabet[j]
                print(str(after[i][j]) + ' nach ' + str(jPrint) + str(iPrint))
                Moveto.loc[countTo] = (str(jPrint) + str(iPrint))
                countTo = countTo + 1
                print(Moveto)
                movementdetected = movementdetected + 1
                print('Changes: ' + str(movementdetected+colorchangedetected))
#Check for ColorChange
            if not type(after[i][j])==int and not type(before[i][j])==int:
                if (str.isupper(after[i][j]) and str.islower(before[i][j])) or (str.islower(after[i][j]) and str.isupper(before[i][j])):
                    iPrint = i + 1
                    jPrint = alphabet[j]
                    print(str(after[i][j]) + ' nach ' + str(jPrint) + str(iPrint))
                    Moveto.loc[countTo] = (str(jPrint) + str(iPrint))
                    countTo = countTo + 1
                    print(Moveto)
                    colorchangedetected = colorchangedetected + 1
                    print('Changes: ' + str(movementdetected+colorchangedetected))
# lange weiße Rochade
        if i == 0: #lange weiße Rochade
            if before[0][4] == 'K' and after[0][2] == 'K' and before[0][0] == 'R'and after[0][3] == 'R':#\
                    #and before[0][1] == 0 and before[0][2] == 0 and before[0][3] == 0\
                    #and after[0][0] == 0 and after[0][1] == 0 and after[0][4] == 0:
                MoveFinal.extend(['e1c1','a1d1'])
                print('Lange weiße Rochade')
# kurze weiße Rochade
        if i == 0: #kurze weiße Rochade
            if before[0][4] == 'K' and after[0][5] == 'R'\
                    and before[0][7] == 'R' and after[0][6] == 'K':#\
                    #and before[0][5] == 0 and before[0][6] == 0 and after[0][4] == 0 and after[0][7] == 0:
                MoveFinal.extend(['e1g1','h1f1'])
                print('Kurze weiße Rochade')
# lange schwarze Rochade
        if i == 7: #lange schwarze Rochade
            if before[7][4] == 'k' and after[7][2] == 'k' and before[7][0] == 'r' and after[7][3] == 'r':# and #\
                    #before[7][1] == 0 and before[7][2] == 0 and before[7][3] == 0 and \
                    #after[7][0] == 0 and after[7][1] == 0 and after[7][4] == 0:
                MoveFinal.extend(['e8c8', 'a8d8'])
                print('Lange schwarze Rochade')
# kurze schwarze Rochade
        if i == 7: #kurze schwarze Rochade
            if before[7][4] == 'k' and after[7][5] == 'r'\
                    and before[7][7] == 'r' and after[7][6] == 'k':#\
                    #and before[7][5] == 0 and before[7][6] == 0 and after[7][4] == 0 and after[7][7] == 0:
                MoveFinal.extend(['e8g8', 'h8f8'])
                print('Kurze schwarze Rochade')


    if movementdetected + colorchangedetected == 2:
        Move.loc[0]=[Movefrom['from'][0],Moveto['to'][0]]
        MoveFinal = Move['from'][0] + Move['to'][0]
        if (countQafter > countQbefore):
            Move.loc[0] = [Movefrom['from'][0], Moveto['to'][0]]
            MoveFinal = Move['from'][0] + Move['to'][0] + 'Q'
        if (countqafter > countqbefore):
            Move.loc[0] = [Movefrom['from'][0], Moveto['to'][0]]
            MoveFinal = Move['from'][0] + Move['to'][0] + 'q'
        if (countNafter > countNbefore):
            Move.loc[0] = [Movefrom['from'][0], Moveto['to'][0]]
            MoveFinal = Move['from'][0] + Move['to'][0] + 'N'
        if (countnafter > countnbefore):
            Move.loc[0] = [Movefrom['from'][0], Moveto['to'][0]]
            MoveFinal = Move['from'][0] + Move['to'][0] + 'n'
    if movementdetected + colorchangedetected <2:
        #print(Move)
        MoveFinal = 0
    if movementdetected + colorchangedetected > 2:
        Move.loc[0] = [Movefrom['from'][0],Moveto['to'][0]]
        Move.loc[1] = [Movefrom['from'][1],Moveto['to'][1]]
        #MoveFinal = 'No clear move without extra if-clause'
    if colorchangedetected > 0:
        Figurschlag = True
    else:
        Figurschlag = False
    #print(Move)
    print(MoveFinal)

    return MoveFinal, Figurschlag

#Figurschlag: *Schlag
#Rochaden: lang:L, kurz: K, weiß: W, schwarz:S
#stockfish.set_fen_position("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
#bestmove=stockfish.get_best_move()
#stockfish.make_moves_from_current_position([ermittelterMove])
#print(stockfish.get_board_visual())