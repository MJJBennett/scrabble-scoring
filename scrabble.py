#!/usr/bin/env python3

import subprocess, json, random, os, sys
from os.path import isfile, join, basename

# Loads json safely
def safe_load_json(path):
    if path is not None and isfile(path):
        with open(path, 'r') as jf:
            return json.load(jf)
    return {}

# Utility function - Prints scores
def print_scores(player_names):
    scores_str = ''
    for key in player_names:
        scores_str += '| ' + key + ': ' + str(player_names[key]) + ' '
    scores_str += '|'
    print(scores_str)

# Holds configuration
class Config:
    def __init__(self):
        self.debug = False
        self.sound_files = []
    def write(self, *args, **kwargs):
        if self.debug:
            print(*args, **kwargs)

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
    return config

# Plays sounds for events
class SoundHandler:
    get_lead = "get_lead"
    lose_lead = "lose_lead"
    win_game = "win_game"
    lose_game = "lose_game"

    def __init__(self, players, config):
        self.sounds_ = {}
        self.config = config
        for pfile in config.sound_files:
            if isfile(pfile):
                self.initialize(pfile, players)
                self.is_init_ = True
                return
        config.write("Could not find a working sound file.")
        self.is_init_ = False
        
    def initialize(self, pfile, players):
        # pfile is guaranteed to be a legitimate file
        with open(pfile, "r") as scfile:
            data = json.load(scfile)
        # we do everything case-insensitive to make things easier
        players = [p.lower() for p in players]
        for data_key in data:
            if data_key.lower() in players:
                self.sounds_[data_key.lower()] = data[data_key]
        
    def play(self, player, kind):
        key = player.lower()
        self.config.write("Attempting to play:", key, kind)
        if key not in self.sounds_:
            self.config.write(key, "not in sounds.")
            return
        if kind not in self.sounds_[key]:
            self.config.write(kind, "not in sounds[" + key + "]")
            return
        if not self.sounds_[key][kind]:
            self.config.write(kind, "is in sounds[" + key + "]", "but has no values. Not playing.")
            return
        sp = random.choice(self.sounds_[key][kind])
        self.config.write("Playing:", sp)
        self.run_sound(["afplay", sp])

    def run_sound(self, sound):
        subprocess.call(sound)

# Gets game data before we begin
def main():
    config = Config()
    for arg in sys.argv:
        if arg in ['-d', '--debug']:
            config.debug = True 
            continue
    config = parse_config(config)
    players = int(input('Number of players: '))
    player_names = {}
    for i in range(1, players+1):
        name = input('Player #' + str(i) + ' name: ')
        player_names[name] = 0
    s = SoundHandler(player_names, config)
    game_loop(player_names, config, s)

class GameState:
    def __init__(self, source_file=None, config=None):
        self.state_ = safe_load_json(source_file)
        self.config_ = config
    def dump_to_temp(self, temp="temp/state_dump.tmp"):
        os.makedirs(os.path.dirname(temp), exist_ok=True)
        with open(temp, "w") as tempfile:
            json.dump(self.state_, tempfile, indent=2)

def game_loop(player_names, config, s):
    rounds = 0
    not_quit = True
    noscore = False
    while not_quit:
        rounds += 1
        for key in player_names:
            print_scores(player_names)
            score = input('Score for ' + key + ': ')
            if score in ['quit', 'exit', 'qu', 'ex']:
                not_quit = False
                break
            if score in ['quitnoscore', 'qns']:
                not_quit = False
                noscore = True
                break
            else:
                try:
                    prev = player_names[key]
                    player_names[key] += int(score)
                    hs = prev   
                    isg = False
                    for key2 in player_names:
                        if key2 != key:
                            if player_names[key2] >= hs:
                                isg = True
                                hs = player_names[key2]
                    if player_names[key] > hs and isg:
                        s.play(key, SoundHandler.get_lead)
                except ValueError:
                    print('Failed to accept the score entered. Please repeat.')

    hs = 0
    hp = "Nobody"
    for pn in player_names:
        if player_names[pn] > hs:
            hp = pn
            hs = player_names[pn]
    s.play(hp, SoundHandler.win_game)

    print(str(player_names))
    print('Rounds: ' + str(rounds))

    if not noscore:
        data = safe_load_json('scores.json')

        game_name = None
        while game_name is None or game_name in data:
            game_name = input('Enter a name for this game: ')

        data[game_name] = player_names
        data[game_name]['Number of rounds'] = rounds

        with open('scores.json', 'w') as file:
            json.dump(data, file, indent=2)

    print("Congratulations to Andrew for his stunning victory!")

if __name__ == "__main__":
    main()
