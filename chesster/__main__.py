import sys
import PyQt5
import os
from chesster.gui.window import Window
qt_path = os.path.dirname(PyQt5.__file__)
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(qt_path, 'Qt/Plugins')
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
