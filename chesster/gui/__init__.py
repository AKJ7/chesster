from PyQt5.QtCore import QSettings, QTranslator, pyqtSignal, pyqtSlot, QObject


class TranslateSignaler(QObject):
    trigger = pyqtSignal(str)

    def connect_signal(self, signaler):
        self.trigger.connect(signaler)

    def emit(self, value: str):
        self.trigger.emit(value)


global_settings = QSettings('chesster', 'main')
translator = QTranslator()
translate_signal = TranslateSignaler()
