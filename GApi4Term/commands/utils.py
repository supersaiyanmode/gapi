import argparse
import os
import re

class MessageType(object):
    def __call__(self, string):
        return MessageType, str(string)

class MessageFileType(argparse.FileType):
    def __init__(self):
        super(MessageFileType, self).__init__("r")

    def __call__(self, path):
        return MessageFileType, super(MessageFileType, self).__call__(path)

class AttachFileType(argparse.FileType):
    def __init__(self):
        super(AttachFileType, self).__init__("rb")

    def __call__(self, path):
        return AttachFileType, super(AttachFileType, self).__call__(path)

class DirType(object):
    def __call__(self, path):
        if os.path.isdir(path) and not os.path.islink(path):
            return DirType, path
        raise argparse.ArgumentTypeError("Not a directory: " + path)

class URLType(object):
    regex = re.compile(
            r'^(?:http|ftp)s?://' # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'
            r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
            r'localhost|' #localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
            r'(?::\d+)?' # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    def __call__(self, url):
        if not self.regex.match(url):
            raise argparse.ArgumentTypeError("Not a valid URL: " + url)
        return URLType, url

class KeyValuePairType(object):
    def __init__(self, sep="="):
        self.sep = sep

    def __call__(self, string):
        try:
            key, value = string.split(self.sep)
            return KeyValuePairType, (key, value)
        except:
            raise argparse.ArgumentTypeError("Invalid format: " + string)
