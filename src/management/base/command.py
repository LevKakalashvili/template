from abc import ABC, abstractmethod
from argparse import ArgumentParser, Namespace

from core.parser import Parser


class AbstractCommand(ABC):
    @abstractmethod
    def execute(self): ...

    @abstractmethod
    def add_arguments(self): ...

    @abstractmethod
    def set_arguments(self): ...


class BaseCommand(AbstractCommand, ABC):
    args: Namespace = None
    help: str = None

    def __init__(self, args: list[str], parser: ArgumentParser):
        self.parser = parser
        self.add_arguments()
        self.set_arguments()
        self.args = self.parser.parse_args(args)

    def set_arguments(self):
        self.parser.add_help = bool(self.help)
        parser = Parser()
        parser.remove_argument("mode")
