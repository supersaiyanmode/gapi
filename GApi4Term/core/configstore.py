import json
import os
import errno

import appdirs

class Config(object):
    def __init__(self):
        self.path = self.get_path()
        try:
            with open(self.path) as f:
                self.config = json.load(f)
        except IOError, e:
            self.config = {
                "APP": {
                    "secret": "oyD8yERRPoRxmimdMWbyAQB4", 
                    "client_id": "848411162677-ai6j41p7jp9bipk95ao4uufe4r25v2k3.apps.googleusercontent.com"
                },
                "ACCOUNTS": {}
            }
            self.update()

    def __getitem__(self, key):
        return self.config[key]
    
    def update(self):
        with open(self.path, "w") as f:
            json.dump(self.config, f, indent=2)


    def get_path(self):
        base = appdirs.user_data_dir("gapi")
	try:
	    os.makedirs(base)
	except OSError as exc:  # Python >2.5
	    if exc.errno == errno.EEXIST and os.path.isdir(base):
		pass
	    else:
		raise
        return os.path.join(base, "config.json")
