# Standard library modules
from json import load
from pathlib import Path
from typing import Any

# Simple type alias for a level as a two dimensional integer array
Level = list[list[int]]


# Function that reads the level files into an array of levels
def read_levels(level_dir: Path) -> list[Level]:
    # If the level directory does not exist, raise an error
    if not level_dir.exists():
        raise FileNotFoundError("Could not find 'levels' directory.")

    # If the level directory isn't a directory, raise an error
    if not level_dir.is_dir():
        raise ValueError("Path 'level_dir' is not a directory.")

    # Initializes the level array
    levels: list[Level] = []

    # Iterates over the level files in the directory and loads the json files
    for level_file in sorted(level_dir.iterdir()):
        # Ensures the file is a json file
        if level_file.suffix != ".json":
            continue

        # Opens the file in read mode
        with level_file.open("r", encoding="utf-8") as file:
            # Reads the file into a json dictionary
            loaded_json: dict[str, Any] = load(file)

            # Add the level grid to the list if the dictionary contains a "grid" key, otherwise skip
            if "grid" not in loaded_json:
                continue

            levels.append(loaded_json["grid"])

    return levels
