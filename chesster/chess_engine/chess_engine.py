import chess
import chess.engine
import chess.pgn
import chess.svg
import numpy as np
import stockfish as stf
import os
import logging
from dotenv import dotenv_values
import asyncio

logger = logging.getLogger(__name__)


class ChessEngine:
    def __init__(self, skill_level=7, threads=2, minimum_thinking_time=0.5, debug=False):
        if debug:
            logging.basicConfig(level=logging.DEBUG)
        logger.info('Starting Chess engine')
        self.board = chess.Board()
        config = dotenv_values('../../.env')
        stockfish_path = config.get('STOCKFISH_PATH', '/usr/games/stockfish')
        logger.info(f'Stockfish path set to: {stockfish_path}')
        self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        self.engine.ping()
        self.engine.configure({'Skill Level': skill_level, 'Threads': threads,
                               'Minimum Thinking Time': minimum_thinking_time})
        logger.info('Chess Engine Initialisation Completed')

    def set_difficulty(self, difficulty: int):
        self.engine.configure({'Skill Level': difficulty})

    def set_move(self, move: str) -> bool:
        uci_move = chess.Move.from_uci(move)
        if uci_move not in self.board.legal_moves:
            return False
        self.board.push(uci_move)
        return True

    def play(self, move_time=1) -> chess.Move:
        result = self.engine.play(self.board, limit=chess.engine.Limit(move_time))
        self.board.push(result.move)
        return result.move

    def get_drawing(self):
        return chess.svg.board(self.board)
