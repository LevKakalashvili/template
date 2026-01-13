import argparse
import glob
import importlib
import os
from types import ModuleType

from core.logger import logger


class Parser:
    parser = argparse.ArgumentParser()

    def get_help_message(self) -> str:
        return "List of modes: " + ", ".join(self.list_of_commands())

    def add_arguments(self):
        self.parser.add_argument(
            "mode",
            nargs="?",
            default="run_restapi",
            help=self.get_help_message(),
        )

    def parse_commands(self, sys_args):
        try:
            self.add_arguments()
            arguments = self.parser.parse_args(sys_args[0:1])
            module: ModuleType = importlib.import_module(f"management.{arguments.mode}")
            cls = module.Command
            command = cls(sys_args[1:], self.parser)
        except Exception as exc:
            logger.error(f"Command not found, please type another command from this 'List of modes'. Details: {exc}")
        else:
            command.execute()

    def remove_argument(self, arg):
        for action in self.parser._actions:
            opts = action.option_strings
            if (opts and opts[0] == arg) or action.dest == arg:
                self.parser._remove_action(action)
                break

        for action in self.parser._action_groups:
            for group_action in action._group_actions:
                opts = group_action.option_strings
                if (opts and opts[0] == arg) or group_action.dest == arg:
                    action._group_actions.remove(group_action)
                    return

    @staticmethod
    def list_of_commands():
        return [
            name[: len(name) - 3]
            for name in map(os.path.basename, glob.glob("./management/*.py"))
            if name[: len(name) - 3] != "__init__"
        ]
