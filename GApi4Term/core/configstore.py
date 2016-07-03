import json

class Config(object):
    def __init__(self, path):
        self.path = path
        with open(path) as f:
            self.config = json.load(f)

    def __getitem__(self, key):
        return self.config[key]
    
    def update(self):
        with open(self.path, "w") as f:
            json.dump(self.config, f, indent=2)
