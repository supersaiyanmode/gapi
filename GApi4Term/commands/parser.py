import argparse

from .accounts import AccountsCommandsHandler
from .email import EmailCommandsHandler
from .drive import DriveCommandsHandler
from .googl import ShortenUrlCommandHandler
from .tasks import TasksCommandsHandler

handlers = [
    AccountsCommandsHandler,
    EmailCommandsHandler,
    DriveCommandsHandler,
    ShortenUrlCommandHandler,
    TasksCommandsHandler,
]

class Parser(object):
    def __init__(self, config):
        self.config = config
        self.parser = argparse.ArgumentParser()
        subparsers = self.parser.add_subparsers()
        for cls in handlers:
            handler = cls()
            parser = subparsers.add_parser(cls.command)
            parser.set_defaults(obj=handler)
            handler.configure_parser(parser)

    def process(self):
        args = self.parser.parse_args()
        args.obj.process(args, self.config)
        

