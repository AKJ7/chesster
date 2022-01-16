from pathlib import Path
import os
from typing import Union
from chesster.master.action import Action
from chesster.master.module import Module
from chesster.Robot.UR10 import UR10Robot
import logging

logger = logging.getLogger(__name__)


class VisualBasedController(Module):
    def __init__(self, robot: UR10Robot, model_path: Union[str, os.PathLike]):
        self.model_path = model_path
        self.robot = robot

    def start(self):
        pass

    def stop(self):
        pass

    def run(self, action: Action):
        pass
