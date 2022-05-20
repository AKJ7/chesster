from PyQt5.QtCore import QSettings, QTranslator, pyqtSignal, pyqtSlot, QObject


class TranslateSignaler(QObject):
    trigger = pyqtSignal(str)

    def connect_signal(self, signaler):
        self.trigger.connect(signaler)

    def emit(self, value: str):
        self.trigger.emit(value)


class ImagePlotSignal(QObject):
    trigger = pyqtSignal([int, object])

    def connect(self, signaler):
        self.trigger.connect(signaler)

    def emit(self, numb, fig):
        self.trigger.emit(numb, fig)


global_settings = QSettings('chesster', 'main')
translator = QTranslator()
translate_signal = TranslateSignaler()
image_plot_signal = ImagePlotSignal()
