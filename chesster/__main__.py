import os
import sys
from chesster.gui.window import Window
from PyQt5.QtWidgets import QApplication
import logging

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logger.info('CHESSter started!')
    app = QApplication(sys.argv)
    thread = main()
    window = Window()
    window.show()
    ret_val = app.exec()
    logger.info('CHESSter exiting ... Have a nice day!')
    sys.exit(ret_val)
