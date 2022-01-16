from typing import Tuple


class Action:
    """
        x = Action()\
            .move((1, 2), (3, 4))\
            .remove((4, 4))\
            .move((3, 4), (6, 3))
    """
    def __init__(self):
        self.__routes = []

    @property
    def routes(self):
        return self.__routes

    def move(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]):
        self.__routes.append([from_pos, to_pos])
        return self

    def remove(self, what: Tuple[int, int]):
        self.__routes.append(what)
        return self
    
    def promote(self, what: Tuple[int, int]):
        self.__routes.append(what)
        return self
