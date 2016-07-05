import argparse

from GApi4Term.core import Drive
from GApi4Term.commands.utils import AttachFileType

class DriveCommandsHandler(object):
    command = "drive"
    help = "Manage Google Drive"

    def configure_parser(self, parser):
        subparsers = parser.add_subparsers()
        parser_public_upload = subparsers.add_parser("instant-share")
        parser_public_upload.set_defaults(handler=self.process_instant_share)

        parser_public_upload.add_argument("files",
                type=AttachFileType(), nargs="+")

    
    def process(self, args, config):
        self.drive = Drive(config["ACCOUNTS"])
        return args.handler(args, config)

    def process_instant_share(self, args, config):
        for typ, f in args.files:
            file_id = self.drive.public_upload(f.name)
            link = self.drive.share_public_link(file_id)
            print "Upload:", f.name, "at:", link

