from GApi4Term.core import URLShortener
from GApi4Term.commands.utils import URLType

class ShortenUrlCommandHandler(object):
    help = "Shorten URLs using goo.gl service."
    command = "shorten-url"

    def configure_parser(self, parser):
        parser.add_argument("long", type=URLType())

    def process(self, args, config):
        print URLShortener(config["ACCOUNTS"]).shorten(args.long)["id"]

