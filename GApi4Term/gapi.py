#!/usr/bin/env python

import sys
import os

from GApi4Term.core import GoogleAccounts
from GApi4Term.core import Config

from GApi4Term.commands import Parser

def main():
    config = Config()
    parser = Parser(config)
    sys.exit(parser.process())


if __name__ == '__main__':
    main()
