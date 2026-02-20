# Import project modules
import colors

# Set screen dimensions
WIDTH: int = 800
HEIGHT: int = 608
DIMENSIONS: tuple[int, int] = (WIDTH, HEIGHT)
SPRITE_SIZE: int = 32  # NOTE: Do not change

# Set screen properties
TARGET_FPS: int = 60
BGCOLOR: colors.Color = colors.WHITE

# Set game properties
CHARGES_PER_BOTTLE: int = 5
START_VIRUSES: int = 5
VIRUSES_PER_LEVEL: int = 3
VIRUS_MIN_SPEED: int = 1
VIRUS_MAX_SPEED: int = 5
PLAYER_SPEED: int = 3
