# Viral Breakout

## About
This is a small little pygame game made for a class I'm currently taking. You play 
as a little character that needs to navigate a maze while avoiding colliding with
viruses that are randomly generated.

## Using themes
Themes are loaded on application start by reading the `themes/` directory. A theme
is simply a subdirectory containing the following six assets:
1. `antibac.png`
2. `bottle.png`
3. `exit.png`
4. `player.png`
5. `virus.png`
6. `wall.png`  

NOTE: The filenames must match the listed filenames **exactly**. If any assets are
missing, or if the filenames don't match, the theme will not be recognized.

## Requirements
NOTE: Older versions *may* work, but these are the only versions on which the game
is tested and confirmed to work as intended.
- pygame-ce 2.5.6
- Python 3.14

## Controls
- Movement: `WASD`
- Place antibac: `L`
- Restart: `N`
