# Python standard library modules:
import random

# Third party modules:
import pygame as pg
from pygame import Clock, Font, Rect, Surface
from pygame.sprite import Group, Sprite

# Project modules
import colors
from levels import LEVELS, Level

# Set screen dimensions
WIDTH: int = 800
HEIGHT: int = 600
DIMENSIONS: tuple[int, int] = (WIDTH, HEIGHT)

# Set screen properties
TARGET_FPS: int = 60
BGCOLOR: colors.Color = colors.WHITE

# Set game properties
CHARGES_PER_BOTTLE: int = 5
START_VIRUSES: int = 5
VIRUSES_PER_LEVEL: int = 3

# Initialize pygame
pg.init()

# Create the fonts used in the game
font_40: Font = pg.font.SysFont("Segoe UI", 40, False, False)

# Create the window
screen: Surface = pg.display.set_mode(DIMENSIONS)
pg.display.set_caption("Viral Breakout")

# Create the clock to keep track of framerate
clock: Clock = Clock()

# Create variables to keep track of the current state
is_running: bool = True
gameover: bool = False
level_complete: bool = False
game_finished: bool = False
level_number: int = 0

# Declare the levels used in the game
levels: list[Level] = LEVELS

# Create sprite groups for the different classes
virus_group: Group[Sprite] = Group()
player_group: Group[Sprite] = Group()
antibac_group: Group[Sprite] = Group()
wall_group: Group[Sprite] = Group()
bottle_group: Group[Sprite] = Group()
exit_group: Group[Sprite] = Group()

# Render the text snippets used in the game
gameover_text: Surface = font_40.render("Game over.", True, colors.RED)
gameover_rect: Rect = gameover_text.get_rect()
gameover_rect.center = (WIDTH // 2, HEIGHT // 2)

level_complete_text: Surface = font_40.render("Level complete!", True, colors.GREEN)
level_complete_rect: Rect = level_complete_text.get_rect()
level_complete_rect.center = (WIDTH // 2, HEIGHT // 2)

complete_text: Surface = font_40.render("Victory! :3", True, colors.BLUE)
complete_text_rect: Rect = level_complete_text.get_rect()
complete_text_rect.center = (WIDTH // 2, HEIGHT // 2)


# The player class
class Player(Sprite):
    # Class initializer
    def __init__(self) -> None:
        # Initialize the parent class attributes
        Sprite.__init__(self)

        # Construct the rect used for the player's hitbox and rendering
        self.image: Surface = pg.image.load("assets/player.png").convert_alpha()
        self.rect: Rect = self.image.get_rect()
        self.rect.x: int = 64
        self.rect.y: int = 32

        # The player's horizontal and vertical speed
        self.vx: int = 0
        self.vy: int = 0

        # Tracks the amount of antibac charges the player has
        self.antibac_count: int = 0

    # Resets the player state and attributes
    def reset(self) -> None:
        self.vx = 0
        self.vy = 0
        self.antibac_count = 0

    # Updates the player
    def update(self) -> None:
        # If the player instance is malformed, throw an error
        if not self.rect:
            raise RuntimeError("Player does not have a valid 'rect' attribute.")

        # Move in the x direction and calculate hits
        self.rect.x += self.vx
        wall_hit_list: list[Sprite] = pg.sprite.spritecollide(self, wall_group, False)

        # Only executes if collision is detected
        if wall_hit_list:
            # If the wall does not have a rect, throw an error
            if not (collision_rect := wall_hit_list[0].rect):
                raise RuntimeError("Player collided with a wall that does not have a valid 'rect' attribute.")

            # Use the player direction to determine where to place the player
            if self.vx > 0:
                self.rect.right = collision_rect.left
            else:
                self.rect.left = collision_rect.right

        # Move in the x direction and calculate hits
        self.rect.y += self.vy
        wall_hit_list: list[Sprite] = pg.sprite.spritecollide(self, wall_group, False)

        # Only executes if collision is detected
        if wall_hit_list:
            # If the wall does not have a rect, throw an error
            if not (collision_rect := wall_hit_list[0].rect):
                raise RuntimeError("Player collided with a wall that does not have a valid 'rect' attribute.")

            # Use the player direction to determine where to place the player
            if self.vy > 0:
                self.rect.bottom = collision_rect.top
            else:
                self.rect.top = collision_rect.bottom

        # Checks to see if the player has collided with a bottle of antibac and adds 5 charges if so
        bottle_hit_list: list[Sprite] = pg.sprite.spritecollide(self, bottle_group, True)
        if bottle_hit_list:
            self.antibac_count += CHARGES_PER_BOTTLE

        # Checks to see if player collided with an exit
        exit_hit_list: list[Sprite] = pg.sprite.spritecollide(self, exit_group, True)
        if exit_hit_list:
            # Get the global level state variables
            global level_complete, level_number

            # Set the global level states to proceed to next level
            level_complete = True
            level_number += 1

            # Reset the level state
            restart() # noqa # ty: ignore

# The virus class
class Virus(Sprite):
    # Class initializer
    def __init__(self, x: int, y: int, vx: int, vy: int) -> None:
        # Initialize the parent class attributes
        Sprite.__init__(self)

        # Construct the rect used for the virus' hitbox and rendering
        self.image: Surface = pg.image.load("assets/virus.png").convert_alpha()
        self.rect: Rect = self.image.get_rect()
        self.rect.x: int = x
        self.rect.y: int = y

        # The player's horizontal and vertical speed
        self.vx: int = vx
        self.vy: int = vy

    # Updates the virus
    def update(self) -> None:
        # If the instance does not have a 'rect' property, throw an error
        if not self.rect:
            raise RuntimeError("Virus does not have a valid 'rect' attribute.")

        # Move in the x direction and calculate hits
        self.rect.x += self.vx
        wall_hit_list: list[Sprite] = pg.sprite.spritecollide(self, wall_group, False)

        # Only executes if collision is detected
        if wall_hit_list:
            # If the wall does not have a rect, throw an error
            if not (collision_rect := wall_hit_list[0].rect):
                raise RuntimeError("Virus collided with a wall that does not have a valid 'rect' attribute.")

            # Use the player direction to determine where to place the player
            if self.vx > 0:
                self.rect.right = collision_rect.left
            else:
                self.rect.left = collision_rect.right

            # Reverse direction
            self.vx *= -1

        # Move in the x direction and calculate hits
        self.rect.y += self.vy
        wall_hit_list: list[Sprite] = pg.sprite.spritecollide(self, wall_group, False)

        # Only executes if collision is detected
        if wall_hit_list:
            # If the wall does not have a rect, throw an error
            if not (collision_rect := wall_hit_list[0].rect):
                raise RuntimeError("Virus collided with a wall that does not have a valid 'rect' attribute.")

            # Use the player direction to determine where to place the player
            if self.vy > 0:
                self.rect.bottom = collision_rect.top
            else:
                self.rect.top = collision_rect.bottom

            # Reverse direction
            self.vy *= -1

        # Check for OOB
        if self.rect.x + 32 > WIDTH or self.rect.x < 0:
            self.vx *= -1
        if self.rect.y + 32 > HEIGHT or self.rect.y < 0:
            self.vy *= -1

# The antibac class (splat, not the bottle)
class Antibac(Sprite):
    # Class initializer
    def __init__(self, x: int, y: int) -> None:
        # Initializes the parent class attributes
        Sprite.__init__(self)

        # Load the image and construct the rect
        self.image: Surface = pg.image.load("assets/antibac.png").convert_alpha()
        self.rect: Rect = self.image.get_rect()
        self.rect.x: int = x
        self.rect.y: int = y

# The wall class
class Wall(Sprite):
    # Class initializer
    def __init__(self, x: int, y: int) -> None:
        # Initialize the parent class attributes
        Sprite.__init__(self)

        # Load the image and construct the rect
        self.image: Surface = pg.image.load("assets/wall.png").convert_alpha()
        self.rect: Rect = self.image.get_rect()
        self.rect.x: int = x
        self.rect.y: int = y

# The bottle class
class Bottle(Sprite):
    # Class initializer
    def __init__(self, x: int, y: int) -> None:
        # Initialize the parent class attributes
        Sprite.__init__(self)

        # Load the image and construct the rect
        self.image: Surface = pg.image.load("assets/bottle.png").convert_alpha()
        self.rect: Rect = self.image.get_rect()
        self.rect.x: int = x
        self.rect.y: int = y

# The exit class
class Exit(Sprite):
    # Class initializer
    def __init__(self, x: int, y: int) -> None:
        # Initialize the parent class attributes
        Sprite.__init__(self)

        # Load the image and construct the rect
        self.image: Surface = pg.image.load("assets/exit.png").convert_alpha()
        self.rect: Rect = self.image.get_rect()
        self.rect.x: int = x
        self.rect.y: int = y

# Resets the level state and restarts
def restart(player: Player) -> None:
    # If the player instance does not have a valid 'rect' attribute, throw an error
    if not player.rect:
        raise RuntimeError("Player does not have a valid 'rect' attribute.")

    # Get the global variables
    global gameover, level_complete, level_number

    # Set the gloal variables
    gameover = False
    level_complete = False

    # Clear all the sprites
    for virus in virus_group:
        virus.kill()
    for antibac in antibac_group:
        antibac.kill()
    for bottle in bottle_group:
        bottle.kill()
    for wall in wall_group:
        wall.kill()
    for exit in exit_group:
        exit.kill()
    player.reset()

    # Generate the viruses
    for i in range(START_VIRUSES + level_number * VIRUSES_PER_LEVEL):
        start_x: int = random.randint(0, WIDTH)
        start_y: int = random.randint(0, HEIGHT)
        start_vx: int = random.randint(1, 8)
        start_vy: int = random.randint(1, 8)

        virus: Virus = Virus(start_x, start_y, start_vx, start_vy)
        virus_group.add(virus)

    # Load the level objects from the level array
    if level_number < len(levels):
        for y, row in enumerate(levels[level_number]):
            for x, value in enumerate(row):
                if value == 1:
                    wall: Wall = Wall(x * 32, y * 32)
                    wall_group.add(wall)
                elif value == 2:
                    bottle: Bottle = Bottle(x * 32, y * 32)
                    bottle_group.add(bottle)
                elif value == 8:
                    player.rect.x = x * 32
                    player.rect.y = y * 32
                elif value == 9:
                    exit: Exit = Exit(x * 32, y * 32)
                    exit_group.add(exit)

    # If level_number is equal to the level array length, the player has completed the game
    else:
        global game_finished
        game_finished = True

# Create the player instance
player: Player = Player()
player_group.add(player)

# If the player rect was not properly created, throw an error
if not player.rect:
    raise RuntimeError("Failed to create 'rect' for player.")

# Restart once to initialize the game
restart(player)

# Keep the game running:
while is_running:
    # Get the keys pressed
    pressed: pg.key.ScancodeWrapper = pg.key.get_pressed()

    # Set the player speed to 0
    player.vx = 0
    player.vy = 0

    # Handle keyboard input for movement
    if pressed[pg.K_w] and not gameover:
        player.vy = -3
    if pressed[pg.K_s] and not gameover:
        player.vy = 3
    if pressed[pg.K_a] and not gameover:
        player.vx = -3
    if pressed[pg.K_d] and not gameover:
        player.vx = 3

    # Check for collision with virus
    player_hit: dict[Sprite, list[Sprite]] = pg.sprite.groupcollide(
        player_group, virus_group,
        True, # The player should be removed on death
        False, # But not the virus
        pg.sprite.collide_mask # ty: ignore
    )

    # If collision is detected, the player has lost
    if player_hit and not gameover:
        gameover = True

    # Check for virus collision with antibac
    virus_hit: dict[Sprite, list[Sprite]] = pg.sprite.groupcollide(
        virus_group, antibac_group,
        True, # The virus should be removed on contact
        True, # So should the antibac
        pg.sprite.collide_mask # ty: ignore
    )

    # Update all the sprites
    virus_group.update()
    player_group.update()
    antibac_group.update()
    exit_group.update()

    # Start the drawing process
    screen.fill(BGCOLOR)
    virus_group.draw(screen)
    player_group.draw(screen)
    antibac_group.draw(screen)
    exit_group.draw(screen)
    bottle_group.draw(screen)
    wall_group.draw(screen)

    # If the game is over, show the gameover text
    if gameover:
        screen.blit(gameover_text, gameover_rect)

    # Or if the player has won, show the victory text
    if game_finished:
        screen.blit(complete_text, complete_text_rect)

    # Tick the clock and update display
    clock.tick(TARGET_FPS)
    pg.display.update()

    # Handle events
    for event in pg.event.get():
        if event.type == pg.QUIT:
            is_running = False

        # Runs if the player releases a key
        if event.type == pg.KEYUP:
            # Only runs if the player has a non-zero antibac count
            if player.antibac_count > 0:
                # If the key released is 'L', place antibac
                if event.key == pg.K_l:
                    antibac: Antibac = Antibac(int(player.rect.x), int(player.rect.y))
                    antibac_group.add(antibac)

            # If the player pressed 'N', start a new game
            if event.key == pg.K_n:
                level_number = 0
                restart(player)

# Uninitialize pygame
pg.quit()
