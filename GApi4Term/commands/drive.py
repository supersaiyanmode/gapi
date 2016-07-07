import argparse

from GApi4Term.core import Drive
from GApi4Term.commands.utils import AttachFileType, DirType

class DriveCommandsHandler(object):
    command = "drive"
    help = "Manage Google Drive"

    def configure_parser(self, parser):
        subparsers = parser.add_subparsers()

        parser_public_upload = subparsers.add_parser("instant-share")
        parser_public_upload.set_defaults(handler=self.process_instant_share)
        parser_public_upload.add_argument("files",
                type=AttachFileType(), nargs="+")
        
        parser_tree = subparsers.add_parser("tree")
        parser_tree.set_defaults(handler=self.process_list_tree)
        parser_tree.add_argument("folder")

        parser_sync = subparsers.add_parser("sync")
        parser_sync.set_defaults(handler=self.process_sync)
        parser_sync.add_argument("local", type=DirType())
        parser_sync.add_argument("drive")
        
 
    def process(self, args, config):
        self.drive = Drive(config["ACCOUNTS"])
        return args.handler(args, config)

    def process_instant_share(self, args, config):
        for typ, f in args.files:
            file_id = self.drive.public_upload(f.name)["id"]
            link = self.drive.share_public_link(file_id)
            print "Upload:", f.name, "at:", link
        return 0

    def process_list_tree(self, args, config):
        drive_folders = self.drive.search(name=args.folder, isFolder=True)
        for folder in drive_folders:
            #print "Recursing into Directory:", folder
            for item, parents in self.drive.iterate_dir(folder["id"]):
                print " "*len(parents), item["name"]
        return 0

    def process_sync(self, args, config):
        _, fs_path = args.local
        drive_path = args.drive
        drive_id = None
        
        res = self.drive.search(isFolder=True, name=drive_path)
        if len(res) > 1:
            print "Multiple folders found on Google Drive."
            return 1
        elif len(res) == 1:
            drive_id = res[0]["id"]

        self.drive.sync_dir(drive_id, fs_path, lambda : None)
        return 0
