from GApi4Term.core import GoogleAccounts

class AccountsCommandsHandler(object):
    command = "account"
    help = "Manage stored Google accounts"

    def configure_parser(self, parser):
        parser.add_argument('action', choices=["add"])

    def process(self, args, config):
        if args.action == "add":
            g = GoogleAccounts(config)
            return g.add()
        return 1
