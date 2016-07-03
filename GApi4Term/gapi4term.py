import sys
import os

from core import GoogleAccounts
from core import Config

from commands import Parser

def main():
    config = Config(os.path.expanduser("~/.config/gapi4term/config.json"))
    parser = Parser(config)
    sys.exit(parser.process())


if __name__ == '__main__':
    main()
