from PyQt5.QtWidgets import QDialog
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QDialog, QLabel, QGroupBox, QRadioButton
from chesster.gui.utils import get_ui_resource_path
from chesster.gui.chess_rules_resources import *
from PyQt5.QtCore import QSettings
import logging

logger = logging.getLogger(__name__)


class ChessOptions(QDialog):
    def __init__(self, parent=None):
        super(ChessOptions, self).__init__(parent)
        ui_path = get_ui_resource_path('options.ui')
        loadUi(ui_path, self)
        self.settings = QSettings('chesster', 'options')
        audio_state = self.settings.value('audioOn', type=bool, defaultValue=True)
        self.audioCheckBox.setChecked(audio_state)
        language = self.settings.value('language', type=str, defaultValue='deutsch')
        for radio_button in self.languageBox.findChildren(QRadioButton):
            if radio_button.text().lower() == language.lower():
                radio_button.setChecked(True)
            else:
                radio_button.setChecked(False)
        logger.info(f'Audio state: {audio_state}, Language: {language}')

    def accept(self) -> None:
        logger.info('Saving user data')
        self.settings.setValue('audioOn', self.audioCheckBox.isChecked())
        for radio_button in self.languageBox.findChildren(QRadioButton):
            if radio_button.isChecked():
                language = radio_button.text().lower()
                self.settings.setValue('language', language)
                logger.info(f'language: {language}')
                break
        super(ChessOptions, self).accept()
