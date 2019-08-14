from os.path import basename, join, isfile
import json

# Holds configuration
class Config:
    def __init__(self):
        self.debug_ = False
        self.extreme_debug_ = False
        self.sound_files = []
        self.sound_file = None
        self.speak_scores = False
        self.prefix = None
    def write(self, *args, **kwargs):
        if self.debug_:
            if self.prefix is not None:
                print(self.prefix, *args, **kwargs)
            else:
                print(*args, **kwargs)
    def debug(self, *args, **kwargs):
        if self.extreme_debug_:
            if self.prefix is not None:
                print(self.prefix, *args, **kwargs)
            else:
                print(*args, **kwargs)

    def set_prefix(self, prefix):
        self.prefix = prefix
    def unset_prefix(self):
        self.prefix = None

    @staticmethod
    def populate_paths(path):
        np = basename(path)
        paths = []
        paths.append(np)
        paths.append(join(".config", np))
        return paths

# Gets some configuration information
def parse_config(config):
    if not isfile(".config/config.json"):
        config.write("Could not find a configuration file.")
        return config
    config.write("Parsing configuration file.")
    with open(".config/config.json", "r") as confile:
        jd = json.load(confile)
    if "soundfile" in jd:
        config.sound_files = Config.populate_paths(jd["soundfile"])
        config.write("Searching for sound files in:", config.sound_files)
    else:
        config.write("Could not find a path for sound file configuration.")
    for pfile in config.sound_files:
        if isfile(pfile):
            config.sound_file = pfile
            break
    return config
