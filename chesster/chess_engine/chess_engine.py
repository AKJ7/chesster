import chess
import chess.engine
import chess.pgn
import chess.svg
import numpy as np
import stockfish as stf
import os
import logging
import asyncio


class ChessEngine:
    def __init__(self, skill_level=7, threads=2, minimum_thinking_time=30, debug=False):
        if debug:
            logging.basicConfig(level=logging.DEBUG)
        self.board = chess.Board()
        print(os.environ.get('STOCKFISH_PATH'))
        self.engine = chess.engine.SimpleEngine.popen_uci('/usr/games/stockfish')
        self.engine.ping()
        self.engine.configure({'Skill Level': skill_level, 'Threads': threads,
                               'Minimum Thinking Time': minimum_thinking_time})
        print(self.engine.options)

    def set_difficulty(self, difficulty: int):
        self.engine.configure({'Skill Level': difficulty})

    def set_move(self, move: str):
        uci_move = chess.Move.from_uci(move)
        if uci_move not in self.board.legal_moves:
            return False
        self.board.push(uci_move)
        return True

    def play(self, move_time=2000):
        result = self.engine.play(self.board, limit=move_time)
        self.board.push(result.move)
        return result.move

    def get_drawing(self):
        return chess.svg.board(self.board)
