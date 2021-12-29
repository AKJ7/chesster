from chesster.Schach_KI.gameplay import *
from chesster.Schach_KI.comparison import *
from stockfish import Stockfish
#stockfish = Stockfish("C:\\Users\\ywoda\\PycharmProjects\\Chesster\\chesster\\stockfish_14.1_win_x64_avx2.exe",
                      #parameters={"Threads": 4, "Minimum Thinking Time":30, "Skill Level": 50})
before=[]
#stockfish.set_fen_position("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
#print(stockfish.get_board_visual())
# MatrixBefore=Funktion Objekterkennung
player_color='w'
VBCcomm = start_game(player_color)
if VBCcomm != []:
    print(VBCcomm)
#while Checkmate == False:
for i in range(200):
    # Spielerzug → warten auf Bestätigung
    # MatrixAfter=Funktion Objekterkennung
    # If Fehler in Matrix (Funktion fehlt)
        #Move=Matrixvergleich(MatrixBefore,MatrixAfter)
    # else:
        #Move=FullMatrixcomp(MatrixBefore,MatrixAfter)
    Move=eval(input('Spielerzug?'))
    Figurschlag=input('Figur geschlagen?')
    VBCcommand,zug_zulässig, SchachSpieler, SchachKI, SchachmattKI, SchachmattSpieler = gameplay(Move, Figurschlag, before, player_color)
    if zug_zulässig == True:
        print('KI is performing the following move(s): ' + str(VBCcommand))#,zug_zulässig)
    else:
        print('Rollbackmove: ' + str(VBCcommand))
    if SchachSpieler==True:
        print('Spieler steht im Schach')
    if SchachKI==True:
        print('KI steht im Schach')
    if SchachmattSpieler==True:
        print('Spieler steht im Schachmatt')
        break
    if SchachmattKI== True:
        print('KI steht im Schachmatt')
        break

print('Game has come to an end')
    # GUI-Ausgabe (Schach
    #Funktion VBC(VBCcommand)
    #If Zug zulässig==True
        #MatrixBefore=MatrixAfter
        #MatrixAfter=Funktion Objekterkennung
        # If Fehler in Matrix (Funktion fehlt)
        # MoveKI=Matrixvergleich(MatrixBefore,MatrixAfter)
        # else:
        # MoveKI=FullMatrixcomp(MatrixBefore,MatrixAfter)
        # MatrixBefore=MatrixAfter


        #(((
        # if MoveKI <> VBCcommand:
            #Funktion Rollback(MoveKI)
            #Funktion VBC   )))



#Funktion Spielstart - Press "Start Game" on GUI
##Output: Skill Level, Spielerfarbe
#Schachfeldinitialisierung durch Spielerfarbe
#Funktion Objekterkennung
##Output: MatrixBEFORE
#Funktion Spielerzugbestätigung
#Funktion Objekterkennung
##Output: MatrixAfter
#Funktion Matrizenvergleich
##Output: Spielerzug, Figurschlag
#Funktion Schach_KI
##Output: Zugzulässigkeit, Roboterzug
#Funktion: VBC
#if Zugzulässigkeit = true
    #MatrixBefore=MatrixAfter
    #Funktion Objekterkennung
    ##Output: MatrixAfter


