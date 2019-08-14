#!/usr/bin/env python3

import subprocess, json, random, os, sys, re
from enum import Enum
from tools import *
from numtospeech import *
from config import *

# Utility function - Prints scores
def print_scores(player_names, c):
    scores_str = ''
    for key in player_names:
        c.set_prefix("speak_number >>")
        speak_number(int(player_names[key]), c)
        c.unset_prefix()
        scores_str += '| ' + key + ': ' + str(player_names[key]) + ' '
    scores_str += '|'
    print(scores_str)

class GameState:
    def __init__(self, source_file=None, config=None):
        self.state_ = safe_load_json(source_file)
        self.config_ = config
        default(self.state_, "num_players", None)
        default(self.state_, "players", None)
        default(self.state_, "num_rounds", 0)
        default(self.state_, "cur_pos", 0)
        default(self.state_, "ordered_players", [k for k in self.state_["players"]] if
        self.state_["players"] is not None else None)
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
    def get_num_players(self):
        return self.state_["num_players"]
    def set_num_players(self, num):
        if self.get_num_players() is not None:
            self.config_.write("Resetting number of players.")
        self.state_["num_players"] = num
    def get_players(self):
        return self.state_["players"]
    def set_players(self, players):
        if self.get_players() is not None:
            self.config_.write("Resetting players entirely.")
        self.state_["players"] = players
    def score_of(self, player):
        return self.get_players()[player] if player in self.get_players() else -1
    def set_score(self, player, score):
        if self.state_["players"] is None:
            self.state_["players"] = {}
            self.config_.write("Creating 'players' dict.")
        if player not in self.state_["players"]:
            self.config_.write("Creating player: " + player)
        self.state_["players"][player] = score
    def get_rounds(self):
        return self.state_["num_rounds"]
    def new_round(self):
        self.state_["num_rounds"] += 1

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
        subprocess.Popen(sound)

# Gets game data before we begin
def main():
    config = Config()
    for arg in sys.argv:
        if re.match(r'-+v(erbose)?', arg) is not None:
            config.debug_ = True 
            continue
        if re.match(r'-+d(ebug)?', arg) is not None:
            config.debug_ = True 
            continue
        if re.match(r'-+ed(ebug)?', arg) is not None:
            config.extreme_debug_ = True 
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
    while gs.get_num_players() is None:
        try:
            n = int(input('Number of players: '))
            gs.set_num_players(n)
        except:
            print("Could not understand the input -",
                  "please input the number of players.")
    if gs.get_players() is None:
        for i in range(1, gs.get_num_players()+1):
            name = input('Player #' + str(i) + ' name: ')
            gs.set_score(name, 0)
    s = SoundHandler(gs.get_players(), config)
    run_game(config, s, state=gs)


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

def run_game(config, s, state):
    config.write("Starting game.")
    game_loop(config, s, state)
    config.write("Game completed with", state.get_rounds(), "rounds.")

    winner = get_winner(state.get_players())
    config.write("Winner calculated:", winner, "- playing sound.")
    s.play(SoundHandler.win_game, player=winner[0])
    config.write("Finished playing sound.")

    print("Final scores:")
    for n in state.get_players():
        print('\t' + str(n) + ":", state.score_of(n))
    print('Rounds: ' + str(state.get_rounds()))

    if get_bool_input("Would you like to record this game?"):
        data = safe_load_json('scores.json')

        game_name = None
        while game_name is None or game_name in data:
            game_name = input('Enter a name for this game: ')

        data[game_name] = state.get_players()
        data[game_name]['Number of rounds'] = state.get_rounds()

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
    CONFIG_MODIFIED = 3
    SAVE_GAME = 4

def get_next_score(player_names, key, config):
    print_scores(player_names, config)
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
        elif command.startswith('ss'):
            config.write("Speaking scores.")
            config.speak_scores = True
            return InputWrapper(command=cm.CONFIG_MODIFIED)
        elif command.startswith('nss'):
            config.write("Not speaking scores.")
            config.speak_scores = False
            return InputWrapper(command=cm.CONFIG_MODIFIED)
        elif command.startswith('sg') or command.startswith('save'):
            config.write("Saving game.")
            return InputWrapper(command=cm.SAVE_GAME)
        else:
            return InputWrapper(command=cm.UNKNOWN, raw=score)

def game_loop(config, s, state):
    config.debug("Entering game loop.")
    while True:
        state.new_round()
        config.debug("Round:", state.get_rounds(), "| Beginning iteration.")
        for key in state.get_players():
            config.debug("> Scoring player:", key)
            while True:
                score = get_next_score(state.get_players(), key, config)
                if score.is_score():
                    # The score entered
                    score = score.get_score()
                    # The high score, before modifications
                    hs = get_hs(state.get_players()) 
                    # The player's score, before modifications
                    prev = state.get_players()[key]
                    state.get_players()[key] += score
                    # The player's score, post-modifications
                    curr = state.get_players()[key]
                    # Play a sound if the score is large
                    if score > 55:
                        s.play(SoundHandler.large_score, key="scores")

                    if hs != 0 and curr == get_hs(state.get_players()) and curr > hs and (prev < hs or
                            value_in(prev, state.get_players())):
                        # Play 'takes the lead' sort of sound
                        s.play(SoundHandler.get_lead, player=key)
                    elif hs == curr and score != 0:
                        # We're now tied
                        s.play(SoundHandler.tie, key="scores")
                    break # Go to next turn
                else:
                    cmd = score.get_command()
                    if cmd == cm.QUIT:
                        return
                    elif cmd == cm.RELOAD_SOUNDS:
                        s.reload()
                        continue
                    elif cmd == cm.SAVE_GAME:
                        state.dump_to_temp()
                        continue
                    elif cmd == cm.UNKNOWN:
                        print("Could not understand input command:", score.get_raw())
                        continue
    return


if __name__ == "__main__":
    main()
