import argparse

from GApi4Term.core import Tasks

class TasksCommandsHandler(object):
    help = "Manage tasks"
    command = "tasks"

    def configure_parser(self, parser):
        subparsers = parser.add_subparsers()

        parser_list = subparsers.add_parser("list")
        parser_list.set_defaults(handler=self.process_list)
        parser_list.add_argument("-l", dest="list", default=None)

        parser_add = subparsers.add_parser("add")
        parser_add.set_defaults(handler=self.process_add)
        parser_add.add_argument("-m", dest="message", required=True)
        parser_add.add_argument("-l", dest="list", default=None)

    def process(self, args, config):
        self.tasks = Tasks(config["ACCOUNTS"])
        return args.handler(args, config)
    
    def process_list(self, args, config):
        items = self.tasks.list_tasks(args.list)
        for x in sorted(items, key=lambda x: x["position"]):
            print "*", x["title"], "[{}]".format(x["status"])

    def process_add(self, args, config):
        pass
