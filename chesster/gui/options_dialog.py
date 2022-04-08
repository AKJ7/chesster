from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QDialog, QLabel, QGroupBox, QRadioButton, QApplication
from chesster.gui.utils import get_ui_resource_path
from chesster.gui.chess_rules_resources import *
import logging
from chesster.gui import translate_signal, global_settings

logger = logging.getLogger(__name__)

language_map = {'en_US': ('english', 'Englisch'),
                'de_DE': ('german', 'Deutsch')}
reversed_language_map = dict((tuple(map(str.lower, v)), k) for k, v in language_map.items())


class ChessOptions(QDialog):
    def __init__(self, parent=None):
        super(ChessOptions, self).__init__(parent)
        ui_path = get_ui_resource_path('options.ui')
        loadUi(ui_path, self)
        self.settings = global_settings
        audio_state = self.settings.value('audioOn', type=bool, defaultValue=True)
        self.audioCheckBox.setChecked(audio_state)
        self.__current_language = self.settings.value('language', type=str,
                                                      defaultValue=f'{list(language_map.keys())[0]}')
        for radio_button in self.languageBox.findChildren(QRadioButton):
            language_name = radio_button.text().lower()
            if language_name in language_map[self.__current_language]:
                radio_button.setChecked(True)
                break
        logger.info(f'Audio state: {audio_state}, Language: {self.__current_language}')

    def accept(self) -> None:
        logger.info('Saving user data')
        self.settings.setValue('audioOn', self.audioCheckBox.isChecked())
        for radio_button in self.languageBox.findChildren(QRadioButton):
            if radio_button.isChecked():
                language = radio_button.text().lower()
                for k in reversed_language_map.keys():
                    if language in k:
                        translate_signal.emit(reversed_language_map[k])
                        self.settings.setValue('language', reversed_language_map[k])
                        logger.info(f'language: {language}')
                        break
        super(ChessOptions, self).accept()
