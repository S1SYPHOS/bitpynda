import io
import os
import json

import yaml


# Creates directory recursively
def create_path(path) -> bool:
    # If it exists already ..
    if os.path.exists(path):
        # .. report pseudo-success
        return True

    try:
        os.makedirs(path)

        # Report success
        return True

    # Guard against race condition
    except OSError:
        pass

    # Report failure
    return False


# Loads YAML data
def load_yaml(file: io.BufferedReader) -> dict:
    try:
        return yaml.safe_load(file)

    except yaml.YAMLError:
        pass

    return {}


# Quick & dirty slugs
def slugify(string: str) -> str:
    # Convert to lowercase
    string = string.lower()

    # Define replacement characters
    replacements = {
        'ä': 'ae',
        'ö': 'oe',
        'ü': 'ue',
        'ß': 'sz',
    }

    for old, new in replacements.items():
        string = string.replace(old, new)

    return string.replace(' ', '-')


def dump_json(data: dict, json_file: str) -> None:
    '''Stores data as given JSON file'''

    # Write data to JSON file
    with open(json_file, 'w') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
