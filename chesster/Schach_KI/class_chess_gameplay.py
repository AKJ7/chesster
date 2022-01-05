import chess
import chess.engine
import chess.pgn
import chess.svg
import pandas as pd
from chesster.Schach_KI.comparison import *
from stockfish import Stockfish
import logging
from dotenv import dotenv_values
import asyncio
import os

logger = logging.getLogger(__name__)


class ChessGameplay:
    def __init__(self, skill_level=10, threads=4, minimum_thinking_time=30, debug=False):
        if debug:
            logging.basicConfig(level=logging.DEBUG)
        logger.info('Starting Chess engine')
        self.board = chess.Board()
        config = dotenv_values('../../.env')
        # config.get('STOCKFISH_PATH', '/usr/games/stockfish')
        project_path = os.path.dirname(os.path.abspath(__file__))
        stockfish_path = os.path.join(project_path, "stockfish_14.1_win_x64_avx2.exe")
        print(stockfish_path)
        logger.info(f'Stockfish path set to: {stockfish_path}')
        self.engine = Stockfish(stockfish_path, parameters={"Threads": threads,
                                                            "Minimum Thinking Time": minimum_thinking_time,
                                                            "Skill Level": skill_level})
        logger.info('Chess Engine Initialisation Completed')

    def get_drawing(self):
        self.board = chess.Board(self.engine.get_fen_position())
        return chess.svg.board(self.board)

    def start_game(self, player_color:str):
        print(player_color)
        if player_color == 'w':
            self.engine.set_fen_position("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
            self.get_drawing()
            print(self.engine.get_board_visual())
            move_command = []
            #  mirrored Game necessary
        elif player_color == 'b':
            #  Schachfigurpositionen # Turn w/b # Rochade # en passent
            #  gespielte Halbzüge seit letztem Bauernzug oder Figurschlag # Nummer nächster Zug (Schwarz: Start bei 1)
            self.engine.set_fen_position("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
            self.get_drawing()
            print(self.engine.get_board_visual())
            best_move = self.engine.get_best_move()
            self.engine.make_moves_from_current_position([best_move])
            self.get_drawing()
            move_command = [best_move]
            print(self.engine.get_board_visual())
            #  optionalVisualOutput here
        else:
            move_command = []
            print('No allowed player color')
        return move_command

    def gameplay(self, move_opponent, before, player_color):
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
            capture_by_ki, move_command = self.proof_ki_capture(before, best_move, move_command)
            en_passant_by_ki, move_command = self.proof_ki_en_passant(best_move, move_command)
            rochade_by_ki, move_command = self.proof_ki_rochade(best_move, move_command)
            promotion_by_ki, move_command, promotion_piece,  = self.proof_ki_promotion(best_move, move_command, capture_by_ki)

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
                print('Special move performed')
                old_position_mirrored = old_position
            if new_position_mirrored == "":
                print('Special move performed')
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
        move_cmd_cap = [move_cmd_till_now]
        # for i in range(0, 8):
        # for j in range(0, 8):
        if before[y][x] != 0:
            print(best_move[2:4])
            print(before[y][x])
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
        move_cmd_ep = [move_cmd_till_now]
        if best_move[2:4] == enpass:
            proof_enpassant = True
            move_cmd_ep = [best_move, best_move[2:3] + best_move[1:2] + "xx"]
        return proof_enpassant, move_cmd_ep

    def proof_ki_rochade(self, best_move, move_cmd_till_now):
    # Check for Rochade by KI and define moves for VBC
        move_cmd_roch = [move_cmd_till_now]
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
        move_cmd_prom = [move_cmd_till_now]
        if len(best_move) == 5:
            proof_prom = True
            for i,n in enumerate(piece_list):
                if best_move[4:5] == n and ki_capture is True:
                    move_cmd_prom = [best_move[2:4] + "xx", best_move[0:4], best_move[2:4] + "xx",
                                        best_move[4:5] + best_move[4:5] + best_move[2:4]]
                elif best_move[4:5] == n:
                    move_cmd_prom = [best_move[0:4], best_move[2:4] + "xx",
                                     best_move[4:5] + best_move[4:5] + best_move[2:4]]
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

    def compute_matrix_from_fen(self):
        # GetMatrixOutOfFenPosition
        compute_before = str(self.engine.get_fen_position())
        compute_before = compute_before.replace(str(8), "00000000")
        compute_before = compute_before.replace(str(7), "0000000")
        compute_before = compute_before.replace(str(6), "000000")
        compute_before = compute_before.replace(str(5), "00000")
        compute_before = compute_before.replace(str(4), "0000")
        compute_before = compute_before.replace(str(3), "000")
        compute_before = compute_before.replace(str(2), "00")
        compute_before = compute_before.replace(str(1), "0")
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
        print(list2)
        return list2

    def matrix_to_fen(self, matrix, player_turn):
        #  Transform Matrix to fenPosition
        fen_string = ""
        for l in range(0, 8):
            for i in range(0, 8):
                fen_string += str(matrix[l][i])
            if l != 7:
                fen_string += str("/")
        fen_string = fen_string.replace("00000000", str(8))
        fen_string = fen_string.replace("0000000", str(7))
        fen_string = fen_string.replace("000000", str(6))
        fen_string = fen_string.replace("00000", str(5))
        fen_string = fen_string.replace("0000", str(4))
        fen_string = fen_string.replace("000", str(3))
        fen_string = fen_string.replace("00", str(2))
        fen_string = fen_string.replace("0", str(1))
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
        return fen_string




