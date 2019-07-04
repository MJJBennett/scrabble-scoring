import json
from os.path import isfile, join, basename

# Gets a boolean value from the user
def get_bool_input(string):
    return input(string + " [y/n]: ").lower() in ['y', 'yes', 't', 'true']

# Checks if a value is in a dictionary (not a key)
def value_in(value, dictionary):
    for k in dictionary:
        if dictionary[k] == value:
            return True
    return False

# Loads json safely
def safe_load_json(path):
    if path is not None and isfile(path):
        with open(path, 'r') as jf:
            return json.load(jf)
    return {}

# Utility function - Sets a default
def default(d, k, v):
    if k not in d:
        d[k] = v
