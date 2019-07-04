#!/usr/bin/env python3

import subprocess, json, random, os, sys, re
from enum import Enum
from tools import *

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
        self.sound_file = None
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
    for pfile in config.sound_files:
        if isfile(pfile):
            config.sound_file = pfile
            break
    return config

# Plays sounds for events
class SoundHandler:
    get_lead = "get_lead"
    lose_lead = "lose_lead"
    win_game = "win_game"
    lose_game = "lose_game"
    tie = "tie_score"
    large_score = "big_score"

    def __init__(self, players, config):
        self.sounds_ = {}
        self.config = config
        if config.sound_file is not None:
            self.initialize(config.sound_file, players)
            self.is_init_ = True
            self.players = players
            self.pfile = config.sound_file
            return
        self.players = None
        self.pfile = None
        config.write("Could not find a working sound file.")
        self.is_init_ = False

    def reload(self):
        if not self.is_init_:
            self.config.write("Sound could not be reloaded; not loaded in the first place.")
        else:
            if not isfile(self.pfile):
                self.config.write("Sound could not be reloaded; file is missing or removed.")
            else:
                self.initialize(self.pfile, self.players)
        
    def initialize(self, pfile, players):
        self.config.write("Initializing sounds from file:", pfile)

        # pfile is guaranteed to be a legitimate file
        with open(pfile, "r") as scfile:
            self.sounds_ = json.load(scfile)
        
    def play(self, kind, key=None, player=None):
        player = player.lower() if player is not None else None
        self.config.write("play() called with kind:", kind, "| player:",
                          player, "| key:", key)

        lookup = self.sounds_
        json_path = "sounds"
        if player is not None:
            if "players" not in lookup:
                self.config.write('"players" is not in sounds.')
                return
            lookup = lookup["players"]
            json_path += '["players"]'
            key = player

        if key not in lookup:
            self.config.write(key, "not in", json_path)
            return
        json_path += '["' + key + '"]'
        lookup = lookup[key]

        if kind not in lookup:
            self.config.write(kind, "not in", json_path)
            return
        if not lookup[kind]:
            self.config.write(kind, "is in", json_path + ", but has no values. Not playing.")
            return
        self.config.write("Choosing from:", lookup[kind])
        sp = random.choice(lookup[kind])
        self.config.write("Playing:", sp)
        self.run_sound(["afplay", sp])
        self.config.write(". . . Finished playing sound.")

    def run_sound(self, sound):
        subprocess.call(sound)

# Gets game data before we begin
def main():
    config = Config()
    for arg in sys.argv:
        if re.match(r'--?v(erbose)?', arg) is not None:
            config.debug = True 
            continue
    config = parse_config(config)
    # We have parsed configuration - Now what do we want to do?
    selection = input("[N]ew Game | [L]oad Game: ")
    if selection.lower() in ['new', 'n', 'new game']:
        # Create a new game:
        gs = GameState(None, config)
    elif selection.lower() in ['load', 'l', 'load game']:
        gs = GameState(input('Filename: '), config)
    else:
        sys.exit("Failed to create game state.")
    players = None
    while players is None:
        try:
            players = int(input('Number of players: '))
        except:
            print("Could not understand the input -",
                  "please input the number of players.")
            players = None
    player_names = {}
    for i in range(1, players+1):
        name = input('Player #' + str(i) + ' name: ')
        player_names[name] = 0
    s = SoundHandler(player_names, config)
    run_game(player_names, config, s, state=gs)

class GameState:
    def __init__(self, source_file=None, config=None):
        self.state_ = safe_load_json(source_file)
        self.config_ = config
        default(self.state_, "num_players", 0)
        default(self.state_, "players", {})
        default(self.state_, "num_rounds", 0)
        default(self.state_, "cur_pos", 0)
        default(self.state_, "ordered_players", [k for k in self.state_["players"]])
    def dump_to_temp(self, temp="temp/state_dump.tmp"):
        os.makedirs(os.path.dirname(temp), exist_ok=True)
        with open(temp, "w") as tempfile:
            self.config_.write("Saved state to temporary file:", temp, "| Beware of overwriting it.")
            json.dump(self.state_, tempfile, indent=2)
    def save(self, name):
        name = os.path.join(".saves/", name)
        os.makedirs(os.path.dirname(name), exist_ok=True)
        with open(temp, "w") as file:
            json.dump(self.state_, file, indent=2)


def get_hs(ledict):
    hs = 0
    for k in ledict:
        if ledict[k] > hs:
            hs = ledict[k]
    return hs

def get_winner(player_names):
    hs = 0
    hp = "Nobody"
    for pn in player_names:
        if player_names[pn] > hs:
            hp = pn
            hs = player_names[pn]
    return [hp, hs]

def run_game(player_names, config, s, state=None):
    config.write("Starting game.")
    rounds = game_loop(player_names, config, s, state)
    config.write("Game completed with", rounds, "rounds.")

    winner = get_winner(player_names)
    config.write("Winner calculated:", winner, "- playing sound.")
    s.play(SoundHandler.win_game, player=winner[0])
    config.write("Finished playing sound.")

    print("Final scores:")
    for n in player_names:
        print('\t' + str(n) + ":", player_names[n])
    print('Rounds: ' + str(rounds))

    if get_bool_input("Would you like to record this game?"):
        data = safe_load_json('scores.json')

        game_name = None
        while game_name is None or game_name in data:
            game_name = input('Enter a name for this game: ')

        data[game_name] = player_names
        data[game_name]['Number of rounds'] = rounds

        with open('scores.json', 'w') as file:
            json.dump(data, file, indent=2)

    print("Congratulations to Andrew for his stunning victory!")

class InputWrapper:
    def __init__(self, command=None, score=None, raw=None):
        self.command = command
        self.score = score
        self.raw = raw
    def is_command(self):
        return self.command is not None
    def is_score(self):
        return self.score is not None
    def get_command(self):
        return self.command
    def get_score(self):
        return self.score
    def get_raw(self):
        return self.raw
    def is_cm(self, command):
        return self.command is not None and self.command == command

class cm(Enum):
    UNKNOWN = 0
    QUIT = 1
    RELOAD_SOUNDS = 2

def get_next_score(player_names, key, config):
    print_scores(player_names)
    score = input('Score for ' + key + ': ')
    try:
        score = int(score)
        # It was a normal score, return it
        config.write("Returning normal score:", score)
        return InputWrapper(score=score)
    except ValueError:
        # Command input
        config.write("Got a potential command:", score)
        command = score.lower()
        if command in ['quit', 'exit', 'qu', 'ex']:
            return InputWrapper(command=cm.QUIT)
        elif command.startswith('sr'):
            print("Reloading sounds.")
            return InputWrapper(command=cm.RELOAD_SOUNDS)
        else:
            return InputWrapper(command=cm.UNKNOWN, raw=score)

def game_loop(player_names, config, s, state):
    rounds = 0
    while True:
        rounds += 1
        for key in player_names:
            score = get_next_score(player_names, key, config)
            if score.is_score():
                # The score entered
                score = score.get_score()
                # The high score, before modifications
                hs = get_hs(player_names) 
                # The player's score, before modifications
                prev = player_names[key]
                player_names[key] += score
                # The player's score, post-modifications
                curr = player_names[key]
                # Play a sound if the score is large
                if score > 55:
                    s.play(SoundHandler.large_score, key="scores")

                if hs != 0 and curr == get_hs(player_names) and curr > hs and (prev < hs or
                        value_in(prev, player_names)):
                    # Play 'takes the lead' sort of sound
                    s.play(SoundHandler.get_lead, player=key)
                elif hs == curr and score != 0:
                    # We're now tied
                    s.play(SoundHandler.tie, key="scores")
            else:
                cmd = score.get_command()
                if cmd == cm.QUIT:
                    return rounds
                elif cmd == cm.RELOAD_SOUNDS:
                    s.reload()
                    continue
                else:
                    print("Could not understand input command:", score.get_raw())
    return rounds


if __name__ == "__main__":
    main()
