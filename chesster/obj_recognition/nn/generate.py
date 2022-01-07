from chesster.obj_recognition.chessboard import ChessBoard
from chesster.obj_recognition.chessboard_recognition import ChessBoardRecognition
from chesster.camera.realSense import RealSenseCamera
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ChessPieceDatasetGenerator:
    def __init__(self, dest: Path, camera: RealSenseCamera, debug=True):
        if debug:
            logging.basicConfig(level=logging.INFO)
        self.dest = dest
        self.camera = camera
        self.previous_image = self.get_image()
        self.board = ChessBoardRecognition.from_image(self.previous_image)

    def generate(self):
        image = self.get_image()
        self.board.determine_changes(self.previous_image, image)

    def get_image(self):
        image = self.camera.capture_color()
        if image is None:
            raise RuntimeError('No image available')
        return image
