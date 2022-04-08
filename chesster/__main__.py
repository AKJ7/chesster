import sys
from chesster.gui.window import Window
from PyQt5.QtWidgets import QApplication
import logging

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    logger.info('CHESSter started!')
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    ret_val = app.exec()
    logger.info('CHESSter exiting ... Have a nice day!')
    sys.exit(ret_val)
