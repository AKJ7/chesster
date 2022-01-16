from abc import ABC, abstractmethod


class Module(ABC):

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass
