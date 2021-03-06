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
    def __init__(self, skill_level=10, elo=False, elo_rating=1350, threads=4, minimum_thinking_time=30, debug=False):
        if debug:
            logging.basicConfig(level=logging.DEBUG)
        logger.info(f'Starting Chess engine')
        self.board = chess.Board()
        self.last_move = ""
        self.arrow = []
        self.dict_fen_positions = {}
        self.overflow = ""
        self.remis = False
        #config = dotenv_values('../../.env')
        # config.get('STOCKFISH_PATH', '/usr/games/stockfish')
        project_path = os.path.dirname(os.path.abspath(__file__))
        stockfish_path = os.path.join(project_path, "stockfish_14.1_win_x64_avx2.exe")
        logger.info(f'Stockfish path set to: {stockfish_path}')
        self.engine = Stockfish(stockfish_path, parameters={"Threads": threads,
                                                            "Minimum Thinking Time": minimum_thinking_time,
                                                            "Skill Level": skill_level})
        self.engine.set_depth(2)
        if elo is True:
            self.engine.set_elo_rating(elo_rating)
        logger.info(f'Chess engine parameters are: {self.engine.get_parameters()}')
        self.engine.set_fen_position("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        logger.info(f'Chess Engine Initialisation Completed')

    def get_drawing(self, last_move: str, proof: bool, player_color: str, hint=False, midgame=False, fen='8/8/8/8/8/8/8/8 w - - 0 1'):
        """Gets the svg-image by setting current Stockfish-FEN in a Python-Chess-Board (based on predefined orientation of object_recognition of the chess board and depending on player_color → mirrors FEN-Position before setting).
        Additionally: Highlight main move with a colored arrow and king red if in chess

        Args:
            last_move: move in UCI-Notation
            proof: Correctness of last_move → influences arrow color (True: green, False: red)
            player_color: pass player_color → influences FEN-Definition
            hint: Flag to influence arrow color (True: grey) if player is given a hint
            midgame: Flag to take take a given FEN-String rather than the actual Stockfish-FEN (positions without both kings aren't allowed in Stockfish and result in an error)
            fen: correct FEN-Position to draw image if Midgame-Start is True
        Returns:
            svg-image
        """

        if len(last_move) == 5:
            last_move = last_move[0:4] + last_move[4].lower()
        if midgame is True:
            self.board = chess.Board(fen)
            logger.info(f'given fen to get_drawing: {fen}')
            return chess.svg.board(self.board, flipped=True)
        else:
            self.board = chess.Board(self.engine.get_fen_position())
            player_turn = self.get_player_turn_from_fen()
            if player_color == 'w':
                self.board = chess.Board(self.mirror_fen())
            if last_move != "":
                self.last_move = chess.Move.from_uci(last_move)
                move_1_int = chess.parse_square(last_move[0:2])
                move_2_int = chess.parse_square(last_move[2:4])
                if hint is True and proof is True:
                    self.arrow = chess.svg.Arrow(move_1_int, move_2_int, color="#888888")
                elif proof is True:
                    self.arrow = chess.svg.Arrow(move_1_int, move_2_int)
                else:
                    self.arrow = chess.svg.Arrow(move_1_int, move_2_int, color="#FF0000")
                if chess.Board.is_into_check(self.board, self.last_move) is True:
                    logger.info(f'board state is in check')
                    if player_turn == 'w':
                        king_square_index = self.board.king(chess.WHITE)
                        print(king_square_index)
                    else:
                        king_square_index = self.board.king(chess.BLACK)
                        print(king_square_index)
                    return chess.svg.board(self.board, orientation=True, check=king_square_index, lastmove=self.last_move, arrows=[self.arrow], flipped=True)
                else:
                    logger.info(f'board state is not in check')
                    return chess.svg.board(self.board, orientation=True, lastmove=self.last_move, arrows=[self.arrow], flipped=True)
            else:
                return chess.svg.board(self.board, flipped=True)

    def chart_data_evaluation(self):
        """Gets the evaluation of the current game status and converts advantage into values useable for a 100%-barchart.

                Returns:
                    value for black, value for white
                        | if type is 'mate' or abs(value) for type 'cp' is higher than a predefined value, a full advantage for one color is defined
                """
        evaluation = self.engine.get_evaluation()
        logger.info(f'{evaluation}')
        DIVIDER = 25.0
        val_w = 50.0
        val_b = 50.0
        if evaluation['type'] == 'cp':
            if evaluation['value'] == 0:
                val_w = 50.0
                val_b = 50.0
            if evaluation['value'] > 0 and evaluation['value'] <= 50*DIVIDER:
                val_w = 50.0 + evaluation['value']/DIVIDER
                val_b = 50.0 - evaluation['value']/DIVIDER
            elif evaluation['value'] < 0 and evaluation['value'] >= -50*DIVIDER:
                val_b = 50.0 + abs(evaluation['value'])/DIVIDER
                val_w = 50.0 - abs(evaluation['value'])/DIVIDER
            elif abs(evaluation['value']) > 50*DIVIDER:
                if evaluation['value'] > 0:
                    val_w = 100.0
                    val_b = 0.0
                elif evaluation['value'] < 0:
                    val_b = 100.0
                    val_w = 0.0
        elif evaluation['type'] == 'mate': 
            if evaluation['value'] > 0:
                val_w = 100.0
                val_b = 0.0
            elif evaluation['value'] < 0:
                val_b = 100.0
                val_w = 0.0
        return val_w, val_b


    def play_opponent(self, move_opponent: list, player_color: str):
        """Checks for Checkmate and Remis, checks player move and defines rollback moves if move was wrong

            Args:
                move_opponent: list of moves (uci-string) done by the player
                player_color: pass player_color → mirror moves
            Returns:
                List of moves to process, if proof is false, else empty list | bools of checkmates and remis'
            """
        logger.info(f'Player move is initiated')
        # Variablendefinition
        move_command = []
        proof = False
        ki_checkmate = False
        player_checkmate = self.proof_checkmate()  # Fall: Start mitten im Spiel und Spielstatus Schachmatt
        remis_by_half_moves, remis_by_triple_occurence, remis_by_stalemate = self.proof_remis()  # Fall: Start mitten im Spiel und Spielstatus Remis bzw. Patt
        if remis_by_half_moves is True or remis_by_triple_occurence is True or remis_by_stalemate is True:
            self.remis = True
        # Konvention System: Orientierung "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR" (Zeile 8/7/6/5/....)
        # Konvention Schachfeld: Orientierung Zeile 1 bei Roboter (Initialisierung unabh. von Spiel)
        ## --> Spiegelung notwendig
        logger.info(f'Player move passed was {move_opponent} (on tableau)')
        if player_color == 'w':
            move_opponent = self.mirrored_play(move_opponent)
        logger.info(f'Player move passed was {move_opponent} (in operating system)')
        if not move_opponent:
            logger.info(f'Empty player move was passed')
            return  # TODO: What to return if empty player move? Does this case occur?
        if player_checkmate is True:
            logger.info(f'Player is checkmate')
            logger.info(f'Player move {move_opponent} therefore was incorrect - Roboter is reseting to default position')
            roll_back_move = self.rollback(move_opponent)  # Zug des Gegenspielers umkehren
            logger.info(f'Player move is computed backwards to: {roll_back_move} (in operating system)')
            if player_color == 'w':  # Ausgabe für Roboter in Schachfeld-Konvention
                move_command = self.mirrored_play(roll_back_move)
                logger.info(f'Backward move from player {move_command} (on tableau)')
            else:
                move_command = roll_back_move
                logger.info(f'Backward move from player {move_command} (on tableau)')
        elif self.remis is True:
            logger.info(f'Game state is Remis')
            logger.info(f'Player move {move_opponent} therefore was incorrect - Roboter is reseting to default position')
            roll_back_move = self.rollback(move_opponent)  # Zug des Gegenspielers umkehren
            logger.info(f'Player move is computed backwards to: {roll_back_move} (in operating system)')
            if player_color == 'w':  # Ausgabe für Roboter in Schachfeld-Konvention
                move_command = self.mirrored_play(roll_back_move)
                logger.info(f'Backward move from player: {move_command} (on tableau)')
            else:
                move_command = roll_back_move
                logger.info(f'Backward move from player: {move_command} (on tableau)')
        else:
            # Korrektheit des Gegnerzuges prüfen
            proof = self.engine.is_move_correct(move_opponent[0])  # Definierender Zug stets an Stelle 1 der Liste
            if proof is True:
                self.engine.make_moves_from_current_position(move_opponent)  # Zug des Gegenspielers System hinzufügen
                print(self.engine.get_board_visual())
                ki_checkmate = self.proof_checkmate()
                remis_by_half_moves, remis_by_triple_occurence, remis_by_stalemate = self.proof_remis()
                logger.info(f'Player move {move_opponent} was correct (in operating system)')
                if player_color == 'w':  # Ausgabe für Roboter in Schachfeld-Konvention
                    move_opponent = self.mirrored_play(move_opponent)
                    logger.info(f'Move from player {move_opponent} (on tableau)')
                else:
                    logger.info(f'Move from player {move_opponent} (on tableau)')
            else:
                logger.info(f'Player move {move_opponent} was incorrect - Roboter is reseting to default position')
                roll_back_move = self.rollback(move_opponent)  # Zug des Gegenspielers umkehren
                logger.info(f'Player move is computed backwards to: {roll_back_move} (in operating system)')
                if player_color == 'w':  # Ausgabe für Roboter in Schachfeld-Konvention
                    move_command = self.mirrored_play(roll_back_move)
                    logger.info(f'Backward move from player {move_command} (on tableau)')
                else:
                    move_command = roll_back_move
                    logger.info(f'Backward move from player {move_command} (on tableau)')

        return move_command, proof, player_checkmate, ki_checkmate, remis_by_half_moves, remis_by_triple_occurence, remis_by_stalemate

    def play_ki(self, before: list, player_color: str, board):
        """Checks for Checkmate and Remis, computes a KI-Move and defines all moves to process

                Args:
                    before: matrix with game state (occupations)
                    player_color: pass player_color → mirror moves and possible en-passant
                    board: object by object recognition with defined states per field
                Returns:
                    List of moves to process | bools of checkmates and remis'
                """
        logger.info(f'KI move is initiated')
        player_checkmate = False
        move_command = []
        best_move_tab = []
        ki_checkmate = self.proof_checkmate()  # Fall: Start mitten im Spiel und Spielstatus Schachmatt
        remis_by_half_moves, remis_by_triple_occurence, remis_by_stalemate = self.proof_remis()
        best_move_sys = self.engine.get_best_move_time(10)  # Zug der KI berechnen
        logger.info(f'KI move uci {best_move_sys} (in operating system)')
        # before = self.compute_matrix_from_fen(player_color)  # wenn Objekte (board) der Objekterkennung nicht verfügbar
        if best_move_sys != None:
            change_list = 'RBNrbn'  # Rook and Bishop are replaced by Queen, same movement possible
            if len(best_move_sys) == 5 and best_move_sys[4:5] in change_list:
                if player_color == 'w':
                    best_move_sys = best_move_sys[0:4] + 'q'
                else:
                    best_move_sys = best_move_sys[0:4] + 'Q'
            best_move_tab = best_move_sys
            # Konvention System: Orientierung "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR" (Zeile 8/7/6/5/....)
            # Konvention Schachfeld: Orientierung Zeile 1 bei Roboter (Initialisierung unabh. von Spiel)
            ## --> Spiegelung notwendig
            if player_color == 'w':
                best_move_tab = self.mirrored_play([best_move_sys])
                best_move_tab = str(best_move_tab[0])
            move_command = [best_move_tab]

            if ki_checkmate is False:
                #  Überprüfe alle Spezialzüge für Ausgabe mehrerer Zuganweisungen an VBC
                #  Prüfung in Schachfeld-Konvention --> best_move_tab
                capture_by_ki, move_command = self.proof_ki_capture(before, best_move_tab, move_command, board)
                # capture_by_ki, move_command = self.proof_ki_capture_with_matrix(before, best_move_tab, move_command, board)  # wenn Objekte (board) der Objekterkennung nicht verfügbar
                en_passant_by_ki, move_command = self.proof_ki_en_passant(best_move_tab, move_command, player_color)
                rochade_by_ki, move_command = self.proof_ki_rochade(best_move_tab, move_command)
                promotion_by_ki, move_command, promotion_piece, = self.proof_ki_promotion(best_move_tab, move_command,
                                                                                        capture_by_ki)
                self.engine.make_moves_from_current_position([best_move_sys])  # Zug der KI System hinzufügen
                print(self.engine.get_board_visual())
                player_checkmate = self.proof_checkmate()  # auf Schachmatt des Spielers überprüfen
                remis_by_half_moves, remis_by_triple_occurence, remis_by_stalemate = self.proof_remis()
                logger.info(f'Check for special moves from KI: "Capture": {capture_by_ki}, "En-Passant": {en_passant_by_ki}, "Rochade": {rochade_by_ki}, "Promotion": {promotion_by_ki}')
                logger.info(f'KI move uci {best_move_sys} (in operating system)')
                logger.info(f'KI move uci {best_move_tab} (on tableau)')
                if player_color == 'w':     # Ausgabe für Logging in beiden Konventionen
                    move_cmd_sys = self.mirrored_play(move_command)
                    logger.info(f'KI moves {move_cmd_sys} (in operating system)')
                    logger.info(f'KI moves {move_command} (on tableau)')
                else:
                    move_cmd_sys = move_command
                    logger.info(f'KI moves {move_cmd_sys} (in operating system)')
                    logger.info(f'KI moves {move_command} (on tableau)')
            else:
                logger.info(f'KI is checkmate')
        return move_command, ki_checkmate, player_checkmate, remis_by_half_moves, remis_by_triple_occurence, remis_by_stalemate
        
    @staticmethod
    def mirroring_matrix():
        """Defines a DataFrame to get mirrored field positions

                Returns:
                    DataFrame with Original to Mirrored
                """
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

    def mirrored_play(self, moves_to_mirror: list):
        """Mirrors a list of passed moves to switch between Stockfish orientation and real orientation

                Args:
                    moves: pass list of moves to mirror
                Returns:
                    List of mirrored moves
                """
        #  Mirror complete move(s) if player is white
        mirrored_position = []
        for n in range(len(moves_to_mirror)):
            mirror_image = self.mirroring_matrix()
            old_position = moves_to_mirror[n][0:2]
            old_position_mirrored = ""
            promotion = ""
            if len(moves_to_mirror[n]) == 5:
                promotion = moves_to_mirror[n][4]
            if len(moves_to_mirror[n]) == 2:
                new_position_mirrored = ""
                new_position = ""
            else:
                new_position = moves_to_mirror[n][2:4]
                new_position_mirrored = ""
            for i in range(0, 64):
                if mirror_image['Original'][i] == old_position:
                    old_position_mirrored = mirror_image['Mirrored'][i]
                if mirror_image['Original'][i] == new_position:
                    new_position_mirrored = mirror_image['Mirrored'][i]
            if old_position_mirrored == "":
                old_position_mirrored = old_position
            if new_position_mirrored == "":
                new_position_mirrored = new_position
            mirrored_position.append(old_position_mirrored + new_position_mirrored + promotion)
        return mirrored_position

    @staticmethod
    def rollback(moves: list):
        """Rollbacks a list of passed move to be executed and define all (rollback) moves to progress from collaborative robot arm. Used to reset wrong moves by player

                Args:
                    moves: pass list of moves to rollback
                Returns:
                    List of move commands
                """
        #  Function to roll back moves if incorrect
        if len(moves[0]) == 5 and len(moves) == 1:  # Fall Bauernumwandlung
            # nur für System notwendiger Zug in Liste moves (z.B. "e7e8Q")
            logger.info(f'Rollback {moves} for case promotion was initiated')
            move1 = moves[0]
            rollback_move1 = move1[2:4] + move1[0:2]
            rollback_move2 = "xx" + move1[2:4]
            rollback_move3 = move1[2:4] + 'P' + move1[4:5]
            rollback_move = [rollback_move3, rollback_move2, rollback_move1]
        elif len(moves[0]) == 5 and len(moves) == 2:  # Fall Bauernumwandlung mit Figurschlag
            # nur für System notwendiger Zug in Liste moves (z.B. "e7e8Q") und Zug für Figurschlag (z.B. "e8xx")
            logger.info(f'Rollback {moves} for case promotion with capture was initiated')
            move1 = moves[0]
            move2 = moves[1]
            rollback_move0 = move2[2:4] + move2[0:2]
            rollback_move1 = move1[2:4] + move1[0:2]
            rollback_move2 = "xx" + move1[2:4]
            rollback_move3 = move1[2:4] + 'P' + move1[4:5]
            rollback_move = [rollback_move3, rollback_move2, rollback_move1, rollback_move0]
        else:
            logger.info(f'Rollback {moves} for case at least one move was initiated')
            move1 = moves[0]
            rollback_move1 = move1[2:4]+move1[0:2]
            rollback_move = [rollback_move1]
            if len(moves) == 1:  # Regulärer Fall: ein Zug
                logger.info(f'Rollback {moves} for case at least one move was initiated')
            elif len(moves) == 2:  # Fall zwei Züge (Figurschlag, En-passant, Rochade)
                logger.info(f'Rollback {moves} for case two moves was initiated')
                move2 = moves[1]
                rollback_move2 = move2[2:4] + move2[0:2]
                rollback_move = [rollback_move2, rollback_move1]
            elif len(moves) == 3:  # Fall drei Züge
                logger.info(f'Rollback {moves} for three moves was initiated')
                move2 = moves[1]
                rollback_move2 = move2[2:4] + move2[0:2]
                move3 = moves[2]
                rollback_move3 = move3[2:4] + move3[0:2]
                rollback_move = [rollback_move3, rollback_move2, rollback_move1]
        logger.info(f'Rollback move(s) is/are: {moves} (in operating system)')
        return rollback_move

    def proof_checkmate(self):
        """Checks for game state "Checkmate"

            Returns:
                True, if state is "Checkmate", else False.
        """
        best_move = self.engine.get_best_move()
        if best_move is None:
            proof = True
        else:
            proof = False
        return proof

    @staticmethod
    def proof_ki_capture(before: list, best_move: str, move_cmd_till_now: list, board):
        """Checks for a capture executed by the KI and add all moves to progress from collaborative robot arm

                Args:
                    best_move: pass executed KI move (in real orientation)
                    move_cmd_till_now: pass move command up to now
                    board: pass board from object recognition Class: ChessBoard
                Returns:
                    True, if capture is executed, else False | New list of move commands, if capture is True, else old list of move commands
                """
        # Check for capturing move
        ##### WARNING: only useable if system is running in integrated mode
        ##### board are objects from obj_recognition
        proof_capture = False
        move_cmd_cap = move_cmd_till_now  # output move_command stays the same as before if no if-clause correct
        field = board.return_field(str(best_move[2:4]))
        state = field.state
        if state != '.':
            logger.info(f'KI captures {state} at {best_move[2:4]} (on tableau)')
            proof_capture = True
            move_cmd_cap = [best_move[2:4] + "xx", best_move]
        return proof_capture, move_cmd_cap

    @staticmethod
    def proof_ki_capture_with_matrix(before: list, best_move: str, move_cmd_till_now: list, board):
        """Checks for a capture executed by the KI and add all moves to progress from collaborative robot arm

                Args:
                    before: pass matrix from function "compute_matrix_from_fen", if no board from object recognition is available
                    best_move: pass executed KI move (in real orientation)
                    move_cmd_till_now: pass move command up to now
                Returns:
                    True, if capture is executed, else False | New list of move commands, if capture is True, else old list of move commands
                """
        # Check for capturing move
        # before und best_move in Schachfeld-Konvention
        x = int(ord(best_move[2])-97)  # Zahl der Buchstaben-Notation in Matrix (0-7)
        y = int(best_move[3])-1  # Zahl der Zahlen-Notation in Matrix (0-7)
        proof_capture = False
        move_cmd_cap = move_cmd_till_now  # output move_command stays the same as before if if-clause is incorrect
        if before[y][x] != ".":
            logger.info(f'KI captures {before[y][x]} at {best_move[2:4]} (on tableau)')
            proof_capture = True
            move_cmd_cap = [best_move[2:4] + "xx", best_move]
        return proof_capture, move_cmd_cap

    def proof_ki_en_passant(self, best_move: str, move_cmd_till_now: list, player_color: str):
        """Checks for an en-passant executed by the KI and add all moves to progress from collaborative robot arm

                Args:
                    best_move: pass executed KI move (in real orientation)
                    move_cmd_till_now: pass move command up to now
                    player_color: pass player_color → mirrors possible en-passant
                Returns:
                    True, if en-passant is executed, else False | New list of move commands, if en-passant is True, else old list of move commands
                """
        # Check for En-Passent by KI
        listing = []
        position = self.engine.get_fen_position()
        for i, n in enumerate(position):
            if n == " ":
                listing.append(i)
        enpass = position[listing[2] + 1:listing[2] + 3]  # get en passant out of fen position (index from space 3)
        if player_color == 'w':
            enpass = self.mirrored_play([enpass])   # mirror possible en-passant due to convention of chess tableau and passed tableau move
        proof_enpassant = False
        move_cmd_ep = move_cmd_till_now  # output move_command stays the same as before if no if-clause correct

        if best_move[2:4] == enpass:
            logger.info(f'KI captures {best_move[2:3] + best_move[1:2]} with En-Passant {enpass} (on tableau)')
            proof_enpassant = True
            move_cmd_ep = [best_move, best_move[2:3] + best_move[1:2] + "xx"]
        return proof_enpassant, move_cmd_ep

    @staticmethod
    def proof_ki_rochade(best_move: str, move_cmd_till_now: list):
        """Checks for a rochade executed by the KI and add all moves to progress from collaborative robot arm

        Args:
            best_move: pass executed KI move (in real orientation)
            move_cmd_till_now: pass move command up to now
        Returns:
            True, if rochade is executed, else False | New list of move commands, if rochade is True, else old list of move commands
        """
    # Check for Rochade by KI
        move_cmd_roch = move_cmd_till_now  # output move_command stays the same as before if no if-clause correct
        proof_roch = False
        if best_move == "e1g1":
            second_move = "h1f1"
            proof_roch = True
            logger.info(f'KI executes short rochade')
        else:
            if best_move == "e1c1":
                second_move = "a1d1"
                proof_roch = True
                logger.info(f'KI executes long rochade')
            else:
                if best_move == "e8g8":
                    second_move = "h8f8"
                    proof_roch = True
                    logger.info(f'KI executes short rochade')
                else:
                    if best_move == "e8c8":
                        second_move = "a8d8"
                        proof_roch = True
                        logger.info(f'KI executes long rochade')
        if proof_roch is True:
            move_cmd_roch = [best_move, second_move]
            logger.info(f'KI executes {move_cmd_roch} to perform rochade (on tableau)')
        return proof_roch, move_cmd_roch

    @staticmethod
    def proof_ki_promotion(best_move: str, move_cmd_till_now: list, ki_capture: bool):
        """Checks for a promotion executed by the KI and add all moves to progress from collaborative robot arm

                Args:
                    best_move: pass executed KI move (in real orientation)
                    move_cmd_till_now: pass move command up to now
                    ki_capture: pass bool return from proof_ki_capture()
                Returns:
                    True, if promotion is executed, else False | New list of move commands, if promotion is True, else old list of move commands | Piece, pawn has been promoted to, if promotion is True, else ""
                """
        # Check for Promotion by KI  and define moves for VBC and return chosen piece
        proof_prom = False
        promotion_piece = ""
        piece_list = ["Q", "q", "N", "n"]
        move_cmd_prom = move_cmd_till_now
        if len(best_move) == 5:
            proof_prom = True
            promotion_piece = best_move[4:5]
            for i, n in enumerate(piece_list):
                if best_move[4:5] == n and ki_capture is True:
                    move_cmd_prom = [best_move[2:4] + "xx", best_move[0:4], best_move[2:4] + "xx",
                                        "P" + best_move[4:5] + best_move[2:4]]
                elif best_move[4:5] == n:
                    move_cmd_prom = [best_move[0:4], best_move[2:4] + "xx",
                                     "P" + best_move[4:5] + best_move[2:4]]
            logger.info(f'Promotion to {promotion_piece} is being performed by KI at {best_move[2:4]} (on tableau)')

        return proof_prom, move_cmd_prom, promotion_piece

    def compute_matrix_from_fen(self, player_color: str): #→ returns matrix with first row white
        """Gets a 8x8 matrix out of the FEN-Position to check for a capture in "proof_ki_capture"

        Args:
            player_color: pass player_color → influences orientation of the matrix (black or white in first row)
        Returns:
            8x8 matrix, if player_color is black, white at the top, else black at top
        """
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
        list_black_top = [[0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0]]
        list_white_top = [[0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0],
                 [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0]]
        for i in range(len(compute_before64)):
            main_divider = int(i / 8)
            rest = int(i % 8)
            list_black_top[main_divider][rest] = compute_before64[i]
        if player_color == 'b':
            count = 7
            for n in range(0, 8):
                list_white_top[n] = list_black_top[count]
                count = count-1
            return list_white_top
        else:
            return list_black_top

    def get_player_turn_from_fen(self):
        """Gets current color for next turn out of FEN-Position

        Returns:
            Color next turn ('b' or 'w')
        """
        # rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
        listing = []
        position = self.engine.get_fen_position()
        for i, n in enumerate(position):
            if n == " ":
                listing.append(i)
        player_turn = position[listing[0] + 1:listing[0] + 2]  # get color out of fen position (index from space 1)
        return player_turn

    def proof_remis(self):
        """Checks for game state "Remis" \n\r
            1.: 50 moves \n\r
            2.: triple occurence \n\r
            3.: stalemate \n\r
            Returns:
                True, if state is "Remis", else False (for every remis possibility ordered as above)
        """
        # rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
        amount = 1
        position = self.engine.get_fen_position()
        remis_by_half_moves = False
        remis_by_triple_occurence = False
        remis_by_stalemate = False
        listing = []
        for i, n in enumerate(position):
            if n == " ":
                listing.append(i)
        count = int(position[listing[3] + 1:listing[4]])  # get number of half moves out of fen position (index from space 4)
        fen_to_enpass = position[0:listing[3]]  # get situation from fen position
        if self.overflow == fen_to_enpass:
            pass
        else:
            self.overflow = fen_to_enpass
            # Dictionary zum Zählen bereits vorhandener Spielsituationen
            if fen_to_enpass in self.dict_fen_positions:
                amount = int(self.dict_fen_positions.get(fen_to_enpass)) + 1
                if amount >= 3:
                    remis_by_triple_occurence = True
                    logger.info(f'Game Status is Remis due to triple occurence')
            self.dict_fen_positions[fen_to_enpass] = amount
        # Aktuelle Halbspielzüge ohne Figurschlag oder Bauernzug aus FEN-Notation
        if count >= 50:
            remis_by_half_moves = True
            logger.info(f'Game Status is Remis due to count of half moves')

        evaluation = self.engine.get_evaluation()
        best_move = self.engine.get_best_move()
        if evaluation['type'] == 'cp' and evaluation['value'] == 0 and best_move is None:
            remis_by_stalemate = True
            logger.info(f'Game Status is Remis due to stalemate')
        return remis_by_half_moves, remis_by_triple_occurence, remis_by_stalemate

    def mirror_fen(self, midgame=False, fen=''):
        """Gets mirrored FEN-Position for function "get_drawing" if player is white due to display game state according to live orientation \n
            e.g.\n\r
            rnbqkbnr/2pppp2/8/8/8/8/2PPPP2/RNBQKBNR w KQkq - 0 1 →\n\r
            RNBQKBNR/2PPPP2/8/8/8/8/2pppp2/rnbqkbnr w KQkq - 0 1 \n\r
        Args:
            midgame: Flag to take take a given FEN-String rather than the actual Stockfish-FEN (positions without both kings aren't allowed in Stockfish and result in an error)
            fen: correct FEN-Position to draw image if Midgame-Start is True
        Returns:
            Mirrored FEN-Position
        """
        if midgame is True:
            fen_old = fen
        else:
            fen_old = str(self.engine.get_fen_position())
        logger.info(f'Original FEN-Position {fen_old}')
        listing_first = []
        for i, n in enumerate(fen_old):
            if n == " ":
                listing_first.append(i)
        board_desc = fen_old[0:listing_first[0]]
        board_desc = board_desc.replace(str(8), "........")
        board_desc = board_desc.replace(str(7), ".......")
        board_desc = board_desc.replace(str(6), "......")
        board_desc = board_desc.replace(str(5), ".....")
        board_desc = board_desc.replace(str(4), "....")
        board_desc = board_desc.replace(str(3), "...")
        board_desc = board_desc.replace(str(2), "..")
        board_desc = board_desc.replace(str(1), ".")
        board_desc = board_desc.replace("/", "")
        mirrored_fen = ""
        for i in range(1, 9):
            for j in range(1,9):
                mirrored_fen += board_desc[63-int(8*int(i)-int(j))]
            if i != 8:
                mirrored_fen += '/'
        mirrored_fen = mirrored_fen.replace("........", str(8))
        mirrored_fen = mirrored_fen.replace(".......", str(7))
        mirrored_fen = mirrored_fen.replace("......", str(6))
        mirrored_fen = mirrored_fen.replace(".....", str(5))
        mirrored_fen = mirrored_fen.replace("....", str(4))
        mirrored_fen = mirrored_fen.replace("...", str(3))
        mirrored_fen = mirrored_fen.replace("..", str(2))
        mirrored_fen = mirrored_fen.replace(".", str(1))
        mirrored_fen += fen_old[listing_first[0]:]
        ## mirror possible en-passant
        listing = []
        for i, n in enumerate(mirrored_fen):
            if n == " ":
                listing.append(i)
        enpass = mirrored_fen[listing[2] + 1:listing[2] + 3]  # get en passent out of fen position (index from space 3)
        enpass_mirr = self.mirrored_play([enpass])
        mirrored_fen = mirrored_fen.replace(enpass, enpass_mirr[0])
        logger.info(f'Mirrored FEN-Position {mirrored_fen}')
        return mirrored_fen

    # not necessary since only possible player_color from GUI are b or w
    def start_game(self, player_color: str):
        print(player_color)
        if player_color == 'w' or player_color == 'b':
            self.engine.set_fen_position("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
            image = self.get_drawing("", True, player_color)
            print(self.engine.get_board_visual())
        else:
            print('No allowed player color')
        return image
    # not useful since it just shows how close a game is to checkmate
    def proof_white_in_chess(self):
        # Check for Status "White is close to Checkmate"
        evaluation = self.engine.get_evaluation()
        if evaluation['type'] == 'mate' and evaluation['value'] > 0:
            proof = True
        else:
            proof = False
        return proof
    # not useful since it just shows how close a game is to checkmate
    def proof_black_in_chess(self):
        # Check for Status "Black is close to Checkmate"
        evaluation = self.engine.get_evaluation()
        if evaluation['type'] == 'mate' and evaluation['value'] < 0:
            proof = True
        else:
            proof = False
        return proof
    # not necessary since object recognition is using a backward calculation and initials a beginning
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
        image = self.get_drawing("", True, player_color)
        #if player_color != player_turn:
        return image #fen_string
    # not necessary since object recognition uses a backward calculation in determine_changes (chessboard.py)
    ## computes moves from given matrices
    def piece_notation_comparison(self, before, after, player_color):
        #  [Zeile1], [Zeile2] etc. aus Robotersicht betrachtet !
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
                        #print('Lange weiße Rochade')
                #   kurze weiße Rochade
                if i == 0:  # kurze weiße Rochade
                    if (before[0][4] == 'K' and after[0][5] == 'R' and before[0][7] == 'R' and after[0][6] == 'K') \
                            or (before[0][4] == 'k' and after[0][5] == 'r' and before[0][7] == 'r' and after[0][
                        6] == 'k') == True:  # \
                        #  and before[0][5] == 0 and before[0][6] == 0 and after[0][4] == 0 and after[0][7] == 0:
                        move_final.extend(['e1g1', 'h1f1'])
                        #print('Kurze weiße Rochade')
                #   lange schwarze Rochade
                if i == 7:  # lange schwarze Rochade
                    if (before[7][4] == 'k' and after[7][2] == 'k' and before[7][0] == 'r' and after[7][3] == 'r') \
                            or (before[7][4] == 'K' and after[7][2] == 'K' and before[7][0] == 'R' and after[7][
                        3] == 'R') == True:  # and #  \
                        #  before[7][1] == 0 and before[7][2] == 0 and before[7][3] == 0 and \
                        #  after[7][0] == 0 and after[7][1] == 0 and after[7][4] == 0:
                        move_final.extend(['e8c8', 'a8d8'])
                        #print('Lange schwarze Rochade')
                #   kurze schwarze Rochade
                if i == 7:  # kurze schwarze Rochade
                    if (before[7][4] == 'k' and after[7][5] == 'r' and before[7][7] == 'r' and after[7][6] == 'k') \
                            or (before[7][4] == 'K' and after[7][5] == 'R' and before[7][7] == 'R' and after[7][
                        6] == 'K') == True:  # \
                        #  and before[7][5] == 0 and before[7][6] == 0 and after[7][4] == 0 and after[7][7] == 0:
                        move_final.extend(['e8g8', 'h8f8'])
                        #print('Kurze schwarze Rochade')

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
            if movement_detected + colorchange_detected >= 4 and move_final == []:
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
    # not necessary since splitted up into play_ki and play_opponent
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
    # not necessary since capturing moves are added while checking for changes in determine_changes (chessboard.py)
    def proof_opponent_capture(self, moves: list, board):
        moves_with_capture = moves
        field = board.return_field(str(moves[0][2:4]))  # Objekt aus Objekterkennung mit Informationen zu Status etc.
        state = field.state
        if state != '.':
            moves_with_capture = [moves[0], moves[0][2:4] + "xx"]
        return moves_with_capture


