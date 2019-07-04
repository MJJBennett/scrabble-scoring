#!/usr/bin/env python3

import json
import subprocess

def max_num():
    return 999

def is_integer(n):
    try:
        x = int(n)
        return True
    except:
        return False

def speak_number_unsafe(n, config):
    if not is_integer(n):
        return False
    if int(n) > max_num():
        return False
    if config.sound_file is None:
        return False

    with open(config.sound_file, 'r') as file:
        j = json.load(file)["numbers"]

    l = [int(c) for c in str(n)]

    playlist = []

    if len(l) == 3:
        playlist.append(j[str(l[0])])
        playlist.append(j["denom"]["hundred"])

    tn = l[-1] if (len(l) == 1 or l[-2] == 0) else (l[-2] * 10 + l[-1])
    # You could play the word "and" here if tn>0, but that takes valuable time
    # So we'll avoid that (especially considered pre-existing gaps between numbers)
    if tn > 19:
        playlist.append(j["dixes"][str(l[-2])])
        playlist.append(j[str(l[-1])])
    elif tn > 0:
        playlist.append(j[str(tn)])

    config.write("Playlist:", playlist)
    for item in playlist:
        subprocess.call(["afplay", item])
    return True

def speak_number(n, c):
    try:
        return speak_number_unsafe(n, c)
    except:
        return False

if __name__ == '__main__':
    import sys
    from scrabble import Config, parse_config
    args = sys.argv[1:]
    c = Config()
    c = parse_config(c)
    c.debug = True
    for arg in args:
        print(speak_number(arg, c))
