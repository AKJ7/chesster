from chesster.Schach_KI.class_chess_gameplay import ChessGameplay
#from chesster.Vision-Based-Control.Vision-Based-Control-Main import *
from chesster.gui.start_dialog import StartDialog
from chesster.gui.game_dialog import GameDialog
from chesster.gui.window import Window
from chesster.gui.chess_rules_dialog import ChessRulesDialog
# ToDo: Implementierung GUI

skill_level = eval(input('Spielstärke (0-20): '))
Chesster = ChessGameplay(skill_level)
player_color = eval(input('Spielerfarbe [w or b]: '))
start_at_some_point = eval(input('Möchtest Du an einer bestimmten Position starten? [yes or no]: '))
if start_at_some_point == 'yes':
    player_turn = eval(input('Welcher Spieler ist am Zug? [w or b]: '))
    starting_matrix = [['R','N','B','Q','K',0,0,0], #first row from robot side # defined matrix is for player black
           [0,'P','P','P','P','P','P',0],
           ['P',0,0,0,0,0,0,0],
           [0,0,0,0,0,0,0,'q'],
           [0,0,0,0,0,0,0,'P'],
           [0,0,0,0,'p',0,0,0],
           ['p','p','p','p',0,'p','p','p'],
           ['r','n','b',0,'k','b','n','r']]
           #ToDo: Funktion Objekterkennung
    Chesster.set_matrix_to_fen(starting_matrix, player_color, player_turn)
else:
    Chesster.start_game(player_color)

Checkmate = False


while Checkmate is False:
    if Chesster.get_player_turn_from_fen() == player_color:
        before = [] #ToDo: Funktion Objekterkennung
        # Spielerzugbestätigung
        after = [] #ToDo: Funktion Objekterkennung
        Move = Chesster.piece_notation_comparison(before,after,player_color)
        Move = eval(input('Spielerzug?'))
        VBC_command, proof_opp_move, ki_in_chess, ki_checkmate = Chesster.play_opponent(Move, player_color)
        if proof_opp_move is True:
            print('Move was correct!')
            if ki_checkmate is True:
                Checkmate = True
                print('Player won. Congrats!')
        else:
            print('Move was incorrect!')
            #ToDo: Funktion VBC
    if Chesster.get_player_turn_from_fen() != player_color:
        before = []  #ToDo: Funktion Objekterkennung
        VBC_command, ki_checkmate, player_checkmate, player_in_chess = Chesster.play_ki(before, player_color)
        if ki_checkmate is True:
            Checkmate = True
            print('Player won. Congrats!')
        elif player_checkmate is True:
            Checkmate = True
            print('KI-Move is now performed by VBC!')
            #ToDo: Funktion VBC
            print('KI won. Nice game! Try again?')
        else:
            print('KI-Move is now performed by VBC!')
            #ToDo: Funktion VBC



    #VBCcommand,zug_zulaessig, SchachSpieler, SchachKI, SchachmattKI, SchachmattSpieler = Chesster.gameplay(Move, before, player_color)
    #if proof_opp_move == True:
    #    print('KI is performing the following move(s): ' + str(VBCcommand))#,zug_zulässig)
    #else:
    #    print('Rollbackmove: ' + str(VBCcommand))
    #if SchachSpieler==True:
    #    print('Spieler steht bald im Schachmatt')
    #if SchachKI==True:
    #    print('KI steht bald im Schachmatt')
    #if SchachmattSpieler==True:
    #    print('Spieler steht im Schachmatt')
    #    Checkmate = True
    #if SchachmattKI== True:
    #    print('KI steht im Schachmatt')
    #    Checkmate = True


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


if __name__ == "__main__":
    pass