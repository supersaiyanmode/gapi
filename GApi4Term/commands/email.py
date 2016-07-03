from itertools import groupby
import argparse

from GApi4Term.core import GMail
from GApi4Term.commands.utils import KeyValuePairType, AttachFileType
from GApi4Term.commands.utils import MessageType, MessageFileType

def prepareKeyValueHTML(args):
    e = lambda x: cgi.escape(unicode(x)).encode('ascii', 'xmlcharrefreplace')
    
    tableStyle = "width:100%;border:1px solid #000;"
    headerStyle = "background-color:#000;color:white;width:50%;"
    fieldCellStyle = "background-color:#eee;color:black;padding:5px;"
    valueCellStyle = "background-color:#fff;color:black;padding:5px;"
    
    rows = ""
    for key, value in args:
        rows += "<tr>"
        rows += "<td style='{fieldCellStyle}'>{key}</td>".format(**locals())
        rows += "<td style='{valueCellStyle}'>{value}</td>".format(**locals())
        rows += "\n"

    
    return """ 
    <html>
        <head>
        </head>
        <body>
        <table style="{tableStyle} {headerStyle}">
        <tr>
        <th>Field</th><th>Value</th>
        </tr>
        {rows}
        </table>
        </body>
    </html>
    """.format(**locals())


class EmailCommandsHandler(object):
    command = "email"
    help = "Manage GMail inbox"

    def configure_parser(self, parser):
        subparsers = parser.add_subparsers()
        parser_send = subparsers.add_parser("send")
        parser_send.set_defaults(handler=self.process_send)

        parser_send.add_argument("-t", "--to", action="append",
                required=True)
        parser_send.add_argument("-m", "--message", 
                action="append", type=MessageType(),
                dest="parts")
        parser_send.add_argument("-a", "--attach",
                action="append", type=AttachFileType(),
                dest="parts")
        parser_send.add_argument("-f", "--file",
                action="append", type=MessageFileType(),
                dest="parts")
        parser_send.add_argument("-k", "--keyvalue",
                action="append", type=KeyValuePairType(),
                dest="parts")
        parser_send.add_argument("-s", "--subject",
                default="Emailed from GAPI4Term", nargs="?")


        parser_list = subparsers.add_parser("list")
        parser_list.set_defaults(handler=self.process_list)

        parser_list.add_argument("-l", "--label", default="inbox")
        parser_list.add_argument("-c", "--count", default=10)
        parser_list.add_argument("-p", "--page", default=0)
        parser_list.add_argument("-q", "--query", default="")


    def process(self, args, config):
        self.gmail = GMail(config["ACCOUNTS"])
        return args.handler(args, config)

    def process_send(self, args, config):
        message = self.gmail.create_message(args.to, args.subject)
        for typ, parts in groupby(args.parts, key=lambda x: x[0]):
            _, parts = zip(*parts)
            if typ == KeyValuePairType:
                message = message.html(prepareKeyValueHTML(parts))
            elif typ == MessageFileType:
                for msgFile in parts:
                    message = message.text(msgFile.read())
            elif typ == AttachFileType:
                for attachFile in parts:
                    message = message.file(attachFile.name)
            elif typ == MessageType:
                for msg in parts:
                    message = message.text(msg)
        res = message.send()
        if res:
            print "Email sent!"
            return 0
        else:
            print "Unable to send email."
            return 1

    def process_list(self, args, config):
        for thread in self.gmail.list(args.page, args.count):
            thread = self.gmail.detail(thread["id"])
            max_width = 80
            print "{:50.50} [{:%Y-%m-%d %H:%M}] ({})".format(
                    thread["subject"],
                    thread["messages"][-1]["time"],
                    len(thread["messages"]))
            for msg in thread["messages"][-5:]:
                s = "    {m[snippet]:46.46} [{m[time]:%Y-%m-%d %H:%m}] ({m[author]})"
                print s.format(m=msg)
        return 0
