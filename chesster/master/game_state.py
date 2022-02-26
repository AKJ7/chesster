from enum import Enum


class ChessboardState(Enum):
    NO_ERROR = 0,
    GENERAL_ERROR = 1,
    CAPTURE = 2,
    PROMOTION = 3,


class PieceColor(Enum):
    WHITE = 'w'
    BLACK = 'b'
