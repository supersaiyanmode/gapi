import argparse

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

class KeyValuePairType(object):
    def __init__(self, sep="="):
        self.sep = sep

    def __call__(self, string):
        try:
            key, value = string.split(self.sep)
            return KeyValuePairType, (key, value)
        except:
            raise argparse.ArgumentTypeError("Invalid format: " + string)
