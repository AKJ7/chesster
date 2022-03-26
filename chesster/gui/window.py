import sys
import signal
import logging
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow, QMessageBox, QStatusBar
from PyQt5.uic import loadUi
from PyQt5.QtCore import QTranslator, QEvent, QLocale
from chesster.gui.window_ui import Ui_MainWindow
from chesster.gui.chess_rules_dialog import ChessRulesDialog
from chesster.gui.start_dialog import StartDialog
from chesster.gui.options_dialog import ChessOptions
from chesster.gui.utils import get_ui_resource_path
from chesster.gui import global_settings, translator, translate_signal
from chesster.gui.calibration_dialog import Calibration

logger = logging.getLogger(__name__)


class Window(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        logger.info('Starting GUI')
        super(Window, self).__init__(parent)
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        self.setupUi(self)
        self.connect_signal_slots()
        self.__translator = QTranslator()
        self.__current_language = ''

    def connect_signal_slots(self):
        self.actionExit.triggered.connect(self.close)
        self.actionAbout.triggered.connect(self.about)
        self.actionChessRules.triggered.connect(self.chess_rules)
        self.actionStart.triggered.connect(self.start_dialog)
        self.actionOptions.triggered.connect(self.options_dialog)
        self.actionCalibration.triggered.connect(self.calibration_dialog)
        translate_signal.connect_signal(self.slot_language_changed)

    def about(self):
        QMessageBox.about(self, 'About CHESSter',
                          '<p>An AI robot chess project</p>'
                          '<p>@2022</p>')

    def chess_rules(self):
        dialog = ChessRulesDialog(self)
        dialog.exec()

    def options_dialog(self):
        dialog = ChessOptions(self)
        dialog.exec()

    def start_dialog(self):
        dialog = StartDialog(self)
        dialog.exec()

    def calibration_dialog(self):
        dialog = Calibration(self)
        dialog.exec()

    def changeEvent(self, a0: QEvent) -> None:
        if a0.type() == QEvent.LanguageChange:
            logger.info('Language changed!')
            self.retranslateUi(self)
        # if a0.type() == QEvent.LocaleChange:
        #     logger.info('Locale Change')
        #     locale_name = QLocale.system().name()
        #     self.load_language(locale_name)
        super(QMainWindow, self).changeEvent(a0)

    def load_language(self, language: str):
        current_language = global_settings.value('language', QLocale.system().name())
        if current_language != language:
            locale = QLocale(current_language)
            QLocale.setDefault(locale)
            language_name = QLocale.languageToString(locale.language())
            filepath = get_ui_resource_path(f'{language}.qm')
            self.switch_translator(translator, str(filepath))
            logger.info(f'Current language in global setting: {current_language}. Switched to: {language_name}')
            return
        logger.info(f'Same language: {current_language}. No action done')

    def slot_language_changed(self, language):
        self.load_language(language)

    @staticmethod
    def switch_translator(transl: QTranslator, filename: str):
        QApplication.removeTranslator(translator)
        if transl.load(filename):
            QApplication.installTranslator(transl)
            logger.info(f'New translator of {filename} successfully installed!')
        else:
            logger.info('Failed to load translator!')

    @staticmethod
    def interrupt_exit(signal_value: int):
        logger.info(f'Interrupt Exit: {signal}')
        sys.exit(signal_value)
