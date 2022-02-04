import chess
import chess.engine
import chess.pgn
import chess.svg
import pandas as pd
from chesster.Schach_KI.comparison import *
from stockfish import Stockfish
import logging
#from dotenv import dotenv_values
import asyncio
import os

logger = logging.getLogger(__name__)


class ChessGameplay:
    def __init__(self, skill_level=10, threads=4, minimum_thinking_time=30, debug=False):
        if debug:
            logging.basicConfig(level=logging.DEBUG)
        logger.info('Starting Chess engine')
        self.board = chess.Board()
        #config = dotenv_values('../../.env')
        # config.get('STOCKFISH_PATH', '/usr/games/stockfish')
        project_path = os.path.dirname(os.path.abspath(__file__))
        stockfish_path = os.path.join(project_path, "stockfish_14.1_win_x64_avx2.exe")
        print(stockfish_path)
        logger.info(f'Stockfish path set to: {stockfish_path}')
        self.engine = Stockfish(stockfish_path, parameters={"Threads": threads,
                                                            "Minimum Thinking Time": minimum_thinking_time,
                                                            "Skill Level": skill_level})
        print(self.engine.get_parameters())
        logger.info('Chess Engine Initialisation Completed')

    def get_drawing(self):
        self.board = chess.Board(self.engine.get_fen_position())
        return chess.svg.board(self.board, flipped=False)

    def start_game(self, player_color:str):
        print(player_color)
        if player_color == 'w' or player_color == 'b':
            self.engine.set_fen_position("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
            image=self.get_drawing()
            print(self.engine.get_board_visual())
        else:
            print('No allowed player color')
        return image
    def play_opponent(self, move_opponent, player_color):
        move_command = []
        ki_in_chess = False
        ki_checkmate = False
        #if player_color == 'w':
        #    move_opponent = self.mirrored_play(move_opponent)
        # print(move_opponent)
        proof = self.engine.is_move_correct(move_opponent[0])
        if proof is True:
            #  Zug des Gegenspielers hinzufügen
            self.engine.make_moves_from_current_position(move_opponent)
            self.get_drawing()
            print(self.engine.get_board_visual())

            #print(self.engine.get_evaluation())
            #print(self.engine.get_fen_position())
            ki_in_chess = self.proof_white_in_chess()
            best_move = self.engine.get_best_move()
            ki_checkmate = self.proof_checkmate(best_move)
            print('move in operating system ' + str(move_opponent))
        else:
            print("move_opponent incorrect - Roboter is reseting to default position")
            roll_back_move = self.rollback(move_opponent)

            if player_color == 'w':
                move_command = self.mirrored_play(roll_back_move)
                print('move on tableau ' + str(move_command))
            else:
                move_command = roll_back_move
                print('move on tableau ' + str(move_command))

        return move_command, proof, ki_in_chess, ki_checkmate

    def play_ki(self, before, player_color):
        best_move = self.engine.get_best_move()
        ki_checkmate = self.proof_checkmate(best_move)
        before = self.compute_matrix_from_fen() #nur Ersatz für nicht vorhandene Funktion Objekterkennung
        #  Zug der KI berechnen, auf Schachmatt der KI überprüfen und Zug Spiel hinzufügen
        best_move = self.engine.get_best_move()
        self.engine.make_moves_from_current_position([best_move])
        self.get_drawing()
        move_command = [best_move]

        #print(self.engine.get_evaluation())
        #print(self.engine.get_fen_position())
        player_in_chess = self.proof_black_in_chess()
        #  auf Schachmatt des Spielers überprüfen
        best_move_opponent = self.engine.get_best_move()
        player_checkmate = self.proof_checkmate(best_move_opponent)

        print(self.engine.get_board_visual())

        #  check for all special moves by KI to give VBC multiple moves to perform
        if ki_checkmate is False:
            capture_by_ki, move_command = self.proof_ki_capture(before, best_move, move_command)
            en_passant_by_ki, move_command = self.proof_ki_en_passant(best_move, move_command)
            rochade_by_ki, move_command = self.proof_ki_rochade(best_move, move_command)
            promotion_by_ki, move_command, promotion_piece, = self.proof_ki_promotion(best_move, move_command,
                                                                                      capture_by_ki)
            if player_color == 'w':
                print('move in operating system ' + str(move_command))
                move_command = self.mirrored_play(move_command)
                print('move on tableau ' + str(move_command))
            else:
                move_command = move_command
                print('move on tableau ' + str(move_command))

        return move_command, ki_checkmate, player_checkmate, player_in_chess

    def old_gameplay(self, move_opponent, before, player_color):
        ki_in_chess = False
        ki_checkmate = False
        player_in_chess = False
        player_checkmate = False
        # if player_color == 'w':
            # move_opponent = mirrored_play(move_opponent)
            # print(move_opponent)
        proof = self.engine.is_move_correct(move_opponent[0])
        if proof is True:
            #  Zug des Gegenspielers hinzufügen
            self.engine.make_moves_from_current_position(move_opponent)
            self.get_drawing()
            print(self.engine.get_board_visual())

            print(self.engine.get_evaluation())
            print(self.engine.get_fen_position())
            ki_in_chess = self.proof_white_in_chess()

            before = self.compute_matrix_from_fen()
            #  Zug der KI berechnen, auf Schachmatt der KI überprüfen und Zug Spiel hinzufügen
            best_move = self.engine.get_best_move()
            ki_checkmate = self.proof_checkmate(best_move)
            self.engine.make_moves_from_current_position([best_move])
            self.get_drawing()
            move_command = [best_move]

            print(self.engine.get_evaluation())
            print(self.engine.get_fen_position())
            player_in_chess = self.proof_black_in_chess()
            #  auf Schachmatt des Spielers überprüfen
            best_move_opponent = self.engine.get_best_move()
            player_checkmate = self.proof_checkmate(best_move_opponent)

            print(self.engine.get_board_visual())

            #  check for all special moves by KI to give VBC multiple moves to perform
            if ki_checkmate is False:
                capture_by_ki, move_command = self.proof_ki_capture(before, best_move, move_command)
                en_passant_by_ki, move_command = self.proof_ki_en_passant(best_move, move_command)
                rochade_by_ki, move_command = self.proof_ki_rochade(best_move, move_command)
                promotion_by_ki, move_command, promotion_piece, = self.proof_ki_promotion(best_move, move_command, capture_by_ki)

            if player_color == 'w':
                move_command = self.mirrored_play(move_command)
            else:
                move_command = move_command
            print(move_command)
        else:
            print("move_opponent incorrect - Roboter is reseting to default position")
            roll_back_move = self.rollback(move_opponent)
            #if player_color == 'w':
                #move_command = mirrored_play(roll_back_move)
            #else:
            move_command = roll_back_move
            print(move_command)

        return move_command, proof, ki_in_chess, player_in_chess, ki_checkmate, player_checkmate

    def mirroring_matrix(self):
        #  Define matrix for mirrored_play, e.g: a8→a1
        mirror_image = pd.DataFrame(columns=['Original', 'Mirrored'])
        letters = {'letter': ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']}
        letters_df = pd.DataFrame(data=letters)
        numbers = {'number': [8, 7, 6, 5, 4, 3, 2, 1]}
        numbers_mirrored = {'number_mirrored': [1, 2, 3, 4, 5, 6, 7, 8]}
        numbers_df = pd.DataFrame(data=numbers)
        numbers_mirrored_df = pd.DataFrame(data=numbers_mirrored)
        for l in range(0, 8):
            for i in range(0, 8):
                letter = letters_df['letter'][i]
                number = numbers_df['number'][l]
                number_str = str(number)
                letter_number = letter+number_str

                number_mirrored = numbers_mirrored_df['number_mirrored'][l]
                number_mirrored_str = str(number_mirrored)
                letter_number_mirrored = letter+number_mirrored_str
                mirror_image.loc[l*8+i] = [letter_number, letter_number_mirrored]
        return mirror_image

    def mirrored_play(self, moves_to_mirror):
        #  Mirror complete move(s) if player is white
        mirrored_position = []
        for n in range(len(moves_to_mirror)):
            mirror_image = self.mirroring_matrix()
            old_position = moves_to_mirror[n][0:2]
            old_position_mirrored = ""
            new_position = moves_to_mirror[n][2:4]
            new_position_mirrored = ""
            for i in range(0, 64):
                if mirror_image['Original'][i] == old_position:
                    old_position_mirrored = mirror_image['Mirrored'][i]
                if mirror_image['Original'][i] == new_position:
                    new_position_mirrored = mirror_image['Mirrored'][i]
            if old_position_mirrored == "":
                #print('Special move performed')
                old_position_mirrored = old_position
            if new_position_mirrored == "":
                #print('Special move performed')
                new_position_mirrored = new_position
            mirrored_position.append(old_position_mirrored + new_position_mirrored)
        return mirrored_position

    def rollback(self,moves):
        #  Function to roll back moves if incorrect
        if len(moves[0]) == 5 and len(moves) == 1:
            move1 = moves[0]
            rollback_move1 = move1[2:4] + move1[0:2]
            rollback_move2 = "xx" + move1[2:4]
            rollback_move3 = move1[2:4] + move1[4:5] + move1[4:5]
            rollback_move = [rollback_move3, rollback_move2, rollback_move1]
        elif len(moves[0]) == 5 and len(moves) == 2:
            move1 = moves[0]
            move2 = moves[1]
            rollback_move0 = move2[2:4] + move2[0:2]
            rollback_move1 = move1[2:4] + move1[0:2]
            rollback_move2 = "xx" + move1[2:4]
            rollback_move3 = move1[2:4] + move1[4:5] + move1[4:5]
            rollback_move = [rollback_move3, rollback_move2, rollback_move1, rollback_move0]
        else:
            move1 = moves[0]
            rollback_move1 = move1[2:4]+move1[0:2]
            rollback_move = [rollback_move1]
            if len(moves) == 2:
                move2 = moves[1]
                rollback_move2 = move2[2:4] + move2[0:2]
                rollback_move = [rollback_move2, rollback_move1]
            elif len(moves) == 3:
                move2 = moves[1]
                rollback_move2 = move2[2:4] + move2[0:2]
                move3 = moves[2]
                rollback_move3 = move3[2:4] + move3[0:2]
                rollback_move = [rollback_move3, rollback_move2, rollback_move1]
        return rollback_move

    def proof_ki_capture(self, before, best_move, move_cmd_till_now):
    #  Check for x of any chess piece and define moves for VBC
        x = int(ord(best_move[2:3])-97)
        y = int(best_move[3:4])-1
        print(x,y)
        proof_capture = False
        move_cmd_cap = move_cmd_till_now
        # for i in range(0, 8):
        # for j in range(0, 8):
        if before[y][x] != ".":
            #print(best_move[2:4])
            #print(before[y][x])
            proof_capture = True
            move_cmd_cap = [best_move[2:4] + "xx", best_move]
        return proof_capture, move_cmd_cap

    def proof_ki_en_passant(self, best_move, move_cmd_till_now):
    # Check for En-Passent by KI and define moves for VBC
        listing = []
        position = self.engine.get_fen_position()
        for i, n in enumerate(position):
            # print(i, n)
            if n == " ":
                # print(i)
                listing.append(i)
        enpass = position[listing[2] + 1:listing[2] + 3]  # get en passent out of fen position (index from space 3)

        proof_enpassant = False
        move_cmd_ep = move_cmd_till_now
        if best_move[2:4] == enpass:
            proof_enpassant = True
            move_cmd_ep = [best_move, best_move[2:3] + best_move[1:2] + "xx"]
        return proof_enpassant, move_cmd_ep

    def proof_ki_rochade(self, best_move, move_cmd_till_now):
    # Check for Rochade by KI and define moves for VBC
        move_cmd_roch = move_cmd_till_now
        proof_roch = False
        if best_move == "e1g1":
            second_move = "h1f1"
            proof_roch = True
        else:
            if best_move == "e1c1":
                second_move = "a1d1"
                proof_roch = True
            else:
                if best_move == "e8g8":
                    second_move = "h8f8"
                    proof_roch = True
                else:
                    if best_move == "e8c8":
                        second_move = "a8d8"
                        proof_roch = True
        if proof_roch is True:
            move_cmd_roch = [best_move, second_move]
        return proof_roch, move_cmd_roch

    def proof_ki_promotion(self, best_move, move_cmd_till_now, ki_capture=False):
    # Check for Promotion by KI  and define moves for VBC and return chosen piece
        proof_prom = False
        promotion_piece = ""
        piece_list = ["Q", "q", "N", "n"]
        move_cmd_prom = move_cmd_till_now
        if len(best_move) == 5:
            proof_prom = True
            promotion_piece = best_move[4:5]
            for i,n in enumerate(piece_list):
                if best_move[4:5] == n and ki_capture is True:
                    move_cmd_prom = [best_move[2:4] + "xx", best_move[0:4], best_move[2:4] + "xx",
                                        "P" + best_move[4:5] + best_move[2:4]]
                elif best_move[4:5] == n:
                    move_cmd_prom = [best_move[0:4], best_move[2:4] + "xx",
                                     "P" + best_move[4:5] + best_move[2:4]]
            print("Protomtion to " + promotion_piece + " is being performed by KI")

        return proof_prom, move_cmd_prom, promotion_piece

    def proof_white_in_chess(self):
        # Check for Status "White is close to Checkmate"
        evaluation = self.engine.get_evaluation()
        if evaluation['type'] == 'mate' and evaluation['value'] > 0:
            proof = True
        else:
            proof = False
        return proof

    def proof_black_in_chess(self):
        # Check for Status "Black is close to Checkmate"
        evaluation = self.engine.get_evaluation()
        if evaluation['type'] == 'mate' and evaluation['value'] < 0:
            proof = True
        else:
            proof = False
        return proof

    def proof_checkmate(self,best_move):
        # Check for Status "is Checkmate"
        if best_move is None:
            proof = True
        else:
            proof = False
        return proof

    def compute_matrix_from_fen(self): #→ returns matrix with first row white
        # GetMatrixOutOfFenPosition
        compute_before = str(self.engine.get_fen_position())
        compute_before = compute_before.replace(str(8), "........")
        compute_before = compute_before.replace(str(7), ".......")
        compute_before = compute_before.replace(str(6), "......")
        compute_before = compute_before.replace(str(5), ".....")
        compute_before = compute_before.replace(str(4), "....")
        compute_before = compute_before.replace(str(3), "...")
        compute_before = compute_before.replace(str(2), "..")
        compute_before = compute_before.replace(str(1), ".")
        compute_before = compute_before.replace("/", "")
        compute_before64 = compute_before[0:64]
        list1 = [[0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0]]
        list2 = [[0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0]]
        for i in range(len(compute_before64)):
            main_divider = int(i / 8)
            rest = int(i % 8)
            #  print(type(compute_before64[i]))
            if compute_before64[i] == '0':
                list1[main_divider][rest] = 0
            else:
                list1[main_divider][rest] = compute_before64[i]
        count = 7
        for n in range(0, 8):
            list2[n] = list1[count]
            count = count-1
        #print(list2)
        return list2

    def set_matrix_to_fen(self, matrix, player_color, player_turn):
        #  Transform Matrix to fenPosition
        if player_color == 'b':
            matrix_mirrored = []
            for m in reversed(matrix):
                matrix_mirrored.extend([m])
            matrix = matrix_mirrored
        fen_string = ""
        for l in range(0, 8):
            for i in range(0, 8):
                fen_string += str(matrix[l][i])
            if l != 7:
                fen_string += str("/")
        fen_string = fen_string.replace("........", str(8))
        fen_string = fen_string.replace(".......", str(7))
        fen_string = fen_string.replace("......", str(6))
        fen_string = fen_string.replace(".....", str(5))
        fen_string = fen_string.replace("....", str(4))
        fen_string = fen_string.replace("...", str(3))
        fen_string = fen_string.replace("..", str(2))
        fen_string = fen_string.replace(".", str(1))
        fen_string += " "
        fen_string += player_turn
        fen_string += " "
        rochade = ""
        if matrix[0][4] == "K":
            if matrix[0][7] == "R":
                rochade += "K"
            if matrix[0][0] == "R":
                rochade += "Q"
        if matrix[7][4] == "k":
            if matrix[7][7] == "r":
                rochade += "k"
            if matrix[7][0] == "r":
                rochade += "q"
        if rochade == "":
            rochade += "-"
        fen_string += rochade
        fen_string += " - "
        fen_string += str(0)
        fen_string += " "
        fen_string += str(1)
        print(fen_string)
        self.engine.set_fen_position(fen_string)
        print(self.engine.get_board_visual())
        image = self.get_drawing()
        #if player_color != player_turn:
        return image #fen_string


    def get_player_turn_from_fen(self):
    # Get color turn of current board situation
        listing = []
        position = self.engine.get_fen_position()
        for i, n in enumerate(position):
            # print(i, n)
            if n == " ":
                # print(i)
                listing.append(i)
        player_turn = position[listing[0] + 1:listing[0] + 2]  # get color out of fen position (index from space 1)
        return player_turn

    #  [Zeile1], [Zeile2] etc. aus Robotersicht betrachtet !
    def piece_notation_comparison(self, before, after, player_color):
        if before == [] or after == []:
            pass
        else:
            if player_color == 'b':
                before_mirrored = []
                after_mirrored = []
                for m in reversed(before):
                    before_mirrored.extend([m])
                for n in reversed(after):
                    after_mirrored.extend([n])
                before = before_mirrored
                after = after_mirrored
            else:
                pass

            move = pd.DataFrame(columns=['from', 'to'])
            move_final = []
            alphabet = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
            #  zahlen = [8, 7, 6, 5, 4, 3, 2, 1]
            move_from = pd.DataFrame(columns=['from'])
            move_to = pd.DataFrame(columns=['to'])
            count_from = 0
            count_to = 0
            movement_detected = 0
            colorchange_detected = 0  # matrix with distinction in colors
            count_N_before = 0
            count_N_after = 0
            count_n_before = 0
            count_n_after = 0
            count_Q_before = 0
            count_Q_after = 0
            count_q_before = 0
            count_q_after = 0
            beaten = []

            for i in range(0, 8):
                for j in range(0, 8):
                    #  Bauernumwandlung
                    if before[i][j] == 'Q':
                        count_Q_before = count_Q_before + 1
                    if after[i][j] == 'Q':
                        count_Q_after = count_Q_after + 1
                    if before[i][j] == 'q':
                        count_q_before = count_q_before + 1
                    if after[i][j] == 'q':
                        count_q_after = count_q_after + 1
                    if before[i][j] == 'N':
                        count_N_before = count_N_before + 1
                    if after[i][j] == 'N':
                        count_N_after = count_N_after + 1
                    if before[i][j] == 'n':
                        count_n_before = count_n_before + 1
                    if after[i][j] == 'n':
                        count_n_after = count_n_after + 1
                    #  print(before[i][j])
                    #  print(after[i][j])
                    #  if before[i][j] is not after[i][j]:
                    #  print(i, j)
                    #  Check for MovementFromPosition
                    if after[i][j] == '.' and before[i][j] != '.':
                        number = i + 1
                        letter = alphabet[j]
                        #print(str(before[i][j]) + ' von ' + str(letter) + str(number))
                        move_from.loc[count_from] = (str(letter) + str(number))
                        #print(move_from)
                        count_from = count_from + 1
                        movement_detected = movement_detected + 1
                        #print('Changes: ' + str(movement_detected + colorchange_detected))
                    #  Check for MovementToPosition
                    if before[i][j] == '.' and after[i][j] != '.':
                        number = i + 1
                        letter = alphabet[j]
                        #print(str(after[i][j]) + ' nach ' + str(letter) + str(number))
                        move_to.loc[count_to] = (str(letter) + str(number))
                        #print(move_to)
                        count_to = count_to + 1
                        movement_detected = movement_detected + 1
                        #print('Changes: ' + str(movement_detected + colorchange_detected))
                    #  Check for ColorChange
                    if not after[i][j] == "." and not before[i][j] == ".":
                        if (str.isupper(after[i][j]) and str.islower(before[i][j])) or (
                                str.islower(after[i][j]) and str.isupper(before[i][j])):
                            number = i + 1
                            letter = alphabet[j]
                            #print(str(after[i][j]) + ' nach ' + str(letter) + str(number))
                            move_to.loc[count_to] = (str(letter) + str(number))
                            beaten = [str(letter) + str(number) + 'xx']
                            count_to = count_to + 1
                            #print(move_to)
                            colorchange_detected = colorchange_detected + 1
                            #print('Changes: ' + str(movement_detected + colorchange_detected))
                #   lange weiße Rochade
                if i == 0:  # lange weiße Rochade
                    if (before[0][4] == 'K' and after[0][2] == 'K' and before[0][0] == 'R' and after[0][3] == 'R') \
                            or (before[0][4] == 'k' and after[0][2] == 'k' and before[0][0] == 'r' and after[0][
                        3] == 'r') == True:  # \
                        #  and before[0][1] == 0 and before[0][2] == 0 and before[0][3] == 0\
                        #  and after[0][0] == 0 and after[0][1] == 0 and after[0][4] == 0:
                        move_final.extend(['e1c1', 'a1d1'])
                        print('Lange weiße Rochade')
                #   kurze weiße Rochade
                if i == 0:  # kurze weiße Rochade
                    if (before[0][4] == 'K' and after[0][5] == 'R' and before[0][7] == 'R' and after[0][6] == 'K') \
                            or (before[0][4] == 'k' and after[0][5] == 'r' and before[0][7] == 'r' and after[0][
                        6] == 'k') == True:  # \
                        #  and before[0][5] == 0 and before[0][6] == 0 and after[0][4] == 0 and after[0][7] == 0:
                        move_final.extend(['e1g1', 'h1f1'])
                        print('Kurze weiße Rochade')
                #   lange schwarze Rochade
                if i == 7:  # lange schwarze Rochade
                    if (before[7][4] == 'k' and after[7][2] == 'k' and before[7][0] == 'r' and after[7][3] == 'r') \
                            or (before[7][4] == 'K' and after[7][2] == 'K' and before[7][0] == 'R' and after[7][
                        3] == 'R') == True:  # and #  \
                        #  before[7][1] == 0 and before[7][2] == 0 and before[7][3] == 0 and \
                        #  after[7][0] == 0 and after[7][1] == 0 and after[7][4] == 0:
                        move_final.extend(['e8c8', 'a8d8'])
                        print('Lange schwarze Rochade')
                #   kurze schwarze Rochade
                if i == 7:  # kurze schwarze Rochade
                    if (before[7][4] == 'k' and after[7][5] == 'r' and before[7][7] == 'r' and after[7][6] == 'k') \
                            or (before[7][4] == 'K' and after[7][5] == 'R' and before[7][7] == 'R' and after[7][
                        6] == 'K') == True:  # \
                        #  and before[7][5] == 0 and before[7][6] == 0 and after[7][4] == 0 and after[7][7] == 0:
                        move_final.extend(['e8g8', 'h8f8'])
                        print('Kurze schwarze Rochade')

            if movement_detected + colorchange_detected == 2:
                move.loc[0] = [move_from['from'][0], move_to['to'][0]]
                move_final = [move['from'][0] + move['to'][0]]
                #  Bauernumwandlung
                if (count_Q_after > count_Q_before):
                    move.loc[0] = [move_from['from'][0], move_to['to'][0]]
                    move_final = [move['from'][0] + move['to'][0] + 'Q']
                    #  if player_color == 'w':
                    #      move_final = move['from'][0] + move['to'][0] + 'q'
                if (count_q_after > count_q_before):
                    move.loc[0] = [move_from['from'][0], move_to['to'][0]]
                    move_final = [move['from'][0] + move['to'][0] + 'q']
                    #  if player_color == 'w':
                    #      move_final = move['from'][0] + move['to'][0] + 'Q'
                if (count_N_after > count_N_before):
                    move.loc[0] = [move_from['from'][0], move_to['to'][0]]
                    move_final = [move['from'][0] + move['to'][0] + 'N']
                    #  if player_color == 'w':
                    #      move_final = move['from'][0] + move['to'][0] + 'n'
                if (count_n_after > count_n_before):
                    move.loc[0] = [move_from['from'][0], move_to['to'][0]]
                    move_final = [move['from'][0] + move['to'][0] + 'n']
                    #  if player_color == 'w':
                    #      move_final = move['from'][0] + move['to'][0] + 'N'
            #  en-passant
            if movement_detected + colorchange_detected == 3:
                if move_to['to'][0][0:1] == move_from['from'][0][0:1]:
                    move_final = [move_from['from'][1] + move_to['to'][0], move_from['from'][0] + "xx"]
                if move_to['to'][0][0:1] == move_from['from'][1][0:1]:
                    move_final = [move_from['from'][0] + move_to['to'][0], move_from['from'][1] + "xx"]
            if movement_detected + colorchange_detected < 2:
                #  print(move)
                move_final = 0
                print(
                    "Zug muss wiederholt werden, keine eindeutige Zuordnung des Zuges möglich. Erkannte Teilbewegungen: " + "Züge von einem Feld weg: " +
                    move_from['from'] + "Züge zu einem Feld: " + move_to['to'])
            if movement_detected + colorchange_detected >= 4:
                move.loc[0] = [move_from['from'][0], move_to['to'][0]]
                move.loc[1] = [move_from['from'][1], move_to['to'][1]]
                print(
                    "Zug muss wiederholt werden, keine eindeutige Zuordnung des Zuges möglich. Erkannte Teilbewegungen: " + "Züge von einem Feld weg: " +
                    move_from['from'] + "Züge zu einem Feld: " + move_to['to'])
                #  move_final = 'No clear move without extra if-clause'
            if colorchange_detected > 0:
                piece_capture = True
                move_final.extend(beaten)
            else:
                piece_capture = False
            #  print(move)
            print(move_final)

            return move_final, piece_capture



