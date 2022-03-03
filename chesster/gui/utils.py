from typing import Union
import os
from pathlib import Path


def get_ui_resource_path(resource: Union[os.PathLike, str]):
    return Path(__file__).parent.absolute() / 'res' / resource


SUPPORTED_CHESS_COLORS = {'weiß': 'white', 'schwarz': 'black'}

CHESS_PIECE_MAP = {'könig': 'k',
                   'dame': 'q',
                   'turm': 'r',
                   'läufer': 'b',
                   'springer': 'n',
                   'bauer': 'p'}
