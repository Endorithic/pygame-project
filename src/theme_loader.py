# Import standard library modules
from pathlib import Path

# Contains all the necessary assets a theme must have to be valid
NEEDED_ASSETS: list[str] = ["antibac", "bottle", "exit", "player", "virus", "wall"]


# Class representing a 'theme'.
class Theme:
    # Declare the member variables for linter support
    __slots__: tuple[str, ...] = ("assets", "is_valid", "missing", "name")

    # Class initializer
    def __init__(self, theme_path: Path) -> None:
        # If the provided path is not a directory, throw an error
        if not theme_path.is_dir():
            raise ValueError("Provided path is not a directory.")

        # A dictionary mapping a sprite name to the asset path.
        self.assets: dict[str, Path] = {}

        # List that keeps track of the missing assets
        self.missing: list[str] = []

        # The name of the theme
        self.name: str = theme_path.stem

        # Iterates over all of the contents of the theme folder to find the asset files
        for entry in theme_path.iterdir():
            # Adds the path to the assets dictionary if the asset is a recognized one
            if entry.stem in NEEDED_ASSETS:
                self.assets[entry.stem] = entry.absolute()

        # Validate the theme
        self.is_valid: bool = True
        for entry in NEEDED_ASSETS:
            # If an asset is missing, invalidate the theme and add the asset to the 'missing' list
            if entry not in self.assets.keys():
                self.is_valid = False
                self.missing.append(entry)


# Function that loads all the available themes
def load_themes(theme_path: Path) -> list[Theme]:
    # If the level directory does not exist, raise an error
    if not theme_path.exists():
        raise FileNotFoundError("Could not find 'themes' directory.")

    # If the level directory isn't a directory, raise an error
    if not theme_path.is_dir():
        raise ValueError("Path 'theme_path' is not a directory.")

    # Initialize a list that contains the themes
    themes: list[Theme] = []

    # Iterate over the themes and add them to the theme list
    for theme_dir in theme_path.iterdir():
        # If the entry is not a directory, i.e. not a theme, skip
        if not theme_dir.is_dir():
            continue

        # Construct a theme object from the directory
        theme: Theme = Theme(theme_dir)

        # If the theme is invalid, skip it.
        if not theme.is_valid:
            continue

        # Otherwise add it.
        themes.append(theme)

    return themes
