# ===========================================
# Module importing
# ===========================================

# Python standard library modules
import os
import random
from pathlib import Path
from typing import cast

# Set environment variable to disable Pygame welcome statement
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

# Third party modules
import pygame as pg
from pygame import Clock, Font, Mask, Rect, Surface
from pygame.key import ScancodeWrapper
from pygame.sprite import Group, Sprite

# Project modules
import colors
import config
from levels import Level, read_levels
from theme_loader import Theme, load_themes

# ===========================================
# Preloading and initialization
# ===========================================

# Defines a variable that stores the path of the project root
project_root: Path = Path(__file__).resolve().parent.parent

# ===========================================
# Theme loading
# ===========================================

# Loads all the available themes
try:
    themes: list[Theme] = load_themes(project_root / "themes")

# If loading the themes failed, exit the program
except (FileNotFoundError, ValueError) as e:
    print(f"Error: {str(e)}")
    exit(1)

# Declare the variable for the held theme
loaded_theme: Theme

# Checks to see that a theme is indeed loaded
if len(themes) < 1:
    print("No theme found... Exiting.")
    exit()

# Print all the themes
print("THEME SELECTOR")
for i, theme in enumerate(themes):
    print(f"{i}: {theme.name}")

# Prompts the user until a theme is selected
while True:
    # Prompt the user to select theme
    try:
        selected: int = int(input("Select theme: "))

    # If the input failed, try again
    except ValueError:
        continue

    # If the selected number is valid, load the theme
    if 0 <= selected < len(themes):
        loaded_theme: Theme = themes[selected]
        break

    print("Invalid input.", end=" ")

# Get the theme asset dictionary
assets: dict[str, Path] = loaded_theme.assets

# ===========================================
# Application initialization
# ===========================================

# Initialize pygame
pg.init()

# Create the fonts used in the game
font_40: Font = pg.font.SysFont("Segoe UI", 40, False, False)
font_30_b: Font = pg.font.SysFont("Segoe UI", 30, True, False)

# Create the window
screen: Surface = pg.display.set_mode(config.DIMENSIONS, pg.SCALED)
pg.display.set_caption("Viral Breakout")

# Create the clock to keep track of framerate
clock: Clock = Clock()

# Cache the images to avoid repeated disk reads
images: dict[str, Surface] = {}
for key, val in assets.items():
    original_image: Surface = pg.image.load(val).convert_alpha()

    # Scales the image to the specified sprite size.
    images[key] = pg.transform.scale(
        original_image, (config.SPRITE_SIZE, config.SPRITE_SIZE)
    )

# Create variables to keep track of the current state
is_running: bool = True
gameover: bool = False
game_finished: bool = False
level_number: int = 0

# Declare the levels used in the game
try:
    levels: list[Level] = read_levels(project_root / "levels")

# If loading the levels failed, exit the program
except (FileNotFoundError, ValueError) as e:
    print(f"Error: {str(e)}")
    exit(1)

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
gameover_rect.center = (config.WIDTH // 2, config.HEIGHT // 2)

complete_text: Surface = font_40.render("Victory! :3", True, colors.BLUE)
complete_text_rect: Rect = complete_text.get_rect()
complete_text_rect.center = (config.WIDTH // 2, config.HEIGHT // 2)

# ===========================================
# Sprite classes
# ===========================================


# The player class
class Player(Sprite):
    # Class initializer
    def __init__(self) -> None:
        # Initialize the parent class attributes
        super().__init__()

        # Construct the rect used for the player's hitbox and rendering
        self.image: Surface = images["player"]
        self.mask: Mask = pg.mask.from_surface(self.image)
        self.rect: Rect = self.image.get_rect()
        self.rect.x: int = 64
        self.rect.y: int = 32

        # The player's horizontal and vertical speed
        self.vx: int = 0
        self.vy: int = 0

        # Tracks the amount of antibac charges the player has
        self.antibac_count: int = 0

        # Tracks the wall currently being held
        self.held_wall: Wall | None = None

        # Tracks the last direction the player moved (facing direction)
        self.facing_x: int = 1
        self.facing_y: int = 0

        # Tracks the invincibility period end time
        self.invincible_until: int = 0

    # Checks whether the player is currently invinvible
    @property
    def is_invincible(self) -> bool:
        return pg.time.get_ticks() < self.invincible_until

    # Resets the player state and attributes
    def reset(self) -> None:
        self.vx = 0
        self.vy = 0
        self.antibac_count = 0
        self.held_wall = None
        self.facing_x = 1
        self.facing_y = 0
        self.invincible_until = pg.time.get_ticks() + config.INVINCIBILITY_DURATION

    # Updates the player
    def update(self) -> None:
        # If the player does not have a rect, throw an error
        if not self.rect:
            raise RuntimeError("Player does not have a valid 'rect' attribute.")

        # Update invincibility visual indicator
        if self.is_invincible:
            # Flashing or lowered alpha
            # If the player does not have an image, throw an error
            if not self.image:
                raise RuntimeError("Player does not have a valid 'image' attribute.")
            self.image.set_alpha(128)
        else:
            # If the player does not have an image, throw an error
            if not self.image:
                raise RuntimeError("Player does not have a valid 'image' attribute.")
            self.image.set_alpha(255)

        # Update the position of the held wall if there is one
        if self.held_wall:
            # If the player does not have a rect, throw an error
            if not self.held_wall.rect:
                raise RuntimeError("Player does not have a valid 'rect' attribute.")

            # Snap it to the position in front of the player aligned to the grid
            target_x = (self.rect.centerx // 32 + self.facing_x) * 32
            target_y = (self.rect.centery // 32 + self.facing_y) * 32

            # Keep the held wall within screen boundaries
            target_x = max(0, min(target_x, config.WIDTH - 32))
            target_y = max(0, min(target_y, config.HEIGHT - 32))

            self.held_wall.rect.x = target_x
            self.held_wall.rect.y = target_y

        # Update facing direction if moving
        if self.vx != 0:
            self.facing_x = 1 if self.vx > 0 else -1
            self.facing_y = 0
        if self.vy != 0:
            self.facing_y = 1 if self.vy > 0 else -1
            # If moving diagonally, we might want to keep horizontal facing
            # but for simplicity, the last non-zero velocity component wins
            # or we can just set both if both are non-zero.
            if self.vx == 0:
                self.facing_x = 0

        # Move in the x direction and calculate hits
        self.rect.x += self.vx
        wall_hit_list: list[Sprite] = pg.sprite.spritecollide(self, wall_group, False)

        # Only executes if collision is detected
        if wall_hit_list:
            # If the wall does not have a rect, throw an error
            if not (collision_rect := wall_hit_list[0].rect):
                raise RuntimeError(
                    "Player collided with a wall that does not have a valid 'rect' attribute."
                )

            # Use the player direction to determine where to place the player
            if self.vx > 0:
                self.rect.right = collision_rect.left
            else:
                self.rect.left = collision_rect.right

        # Move in the y direction and calculate hits
        self.rect.y += self.vy
        wall_hit_list: list[Sprite] = pg.sprite.spritecollide(self, wall_group, False)

        # Only executes if collision is detected
        if wall_hit_list:
            # If the wall does not have a rect, throw an error
            if not (collision_rect := wall_hit_list[0].rect):
                raise RuntimeError(
                    "Player collided with a wall that does not have a valid 'rect' attribute."
                )

            # Use the player direction to determine where to place the player
            if self.vy > 0:
                self.rect.bottom = collision_rect.top
            else:
                self.rect.top = collision_rect.bottom

        # Keep the player within the screen boundaries
        if self.rect.left < 0:
            self.rect.left = 0
        elif self.rect.right > config.WIDTH:
            self.rect.right = config.WIDTH

        if self.rect.top < 0:
            self.rect.top = 0
        elif self.rect.bottom > config.HEIGHT:
            self.rect.bottom = config.HEIGHT

        # Checks to see if the player has collided with a bottle of antibac and adds 5 charges if so
        bottle_hit_list: list[Sprite] = pg.sprite.spritecollide(
            self, bottle_group, True
        )
        if bottle_hit_list:
            self.antibac_count += config.CHARGES_PER_BOTTLE

        # Checks to see if player collided with an exit
        exit_hit_list: list[Sprite] = pg.sprite.spritecollide(self, exit_group, True)
        if exit_hit_list and not gameover:
            # Get the global level state variables
            global level_number

            # Set the global level states to proceed to next level
            level_number += 1

            # Reset the level state
            restart(self)


# The virus class
class Virus(Sprite):
    # Class initializer
    def __init__(self, x: int, y: int, vx: int, vy: int) -> None:
        # Initialize the parent class attributes
        super().__init__()

        # Construct the rect used for the virus' hitbox and rendering
        self.image: Surface = images["virus"]
        self.mask: Mask = pg.mask.from_surface(self.image)
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
                raise RuntimeError(
                    "Virus collided with a wall that does not have a valid 'rect' attribute."
                )

            # Use the player direction to determine where to place the player
            if self.vx > 0:
                self.rect.right = collision_rect.left
            else:
                self.rect.left = collision_rect.right

            # Reverse direction
            self.vx *= -1

        # Check for OOB ONLY if no wall collision occurred in x-direction
        elif self.rect.left < 0 or self.rect.right > config.WIDTH:
            self.vx *= -1

        # Move in the y direction and calculate hits
        self.rect.y += self.vy
        wall_hit_list: list[Sprite] = pg.sprite.spritecollide(self, wall_group, False)

        # Only executes if collision is detected
        if wall_hit_list:
            # If the wall does not have a rect, throw an error
            if not (collision_rect := wall_hit_list[0].rect):
                raise RuntimeError(
                    "Virus collided with a wall that does not have a valid 'rect' attribute."
                )

            # Use the player direction to determine where to place the player
            if self.vy > 0:
                self.rect.bottom = collision_rect.top
            else:
                self.rect.top = collision_rect.bottom

            # Reverse direction
            self.vy *= -1

        # Check for OOB only if no wall collision occurred in y-direction
        elif self.rect.top < 0 or self.rect.bottom > config.HEIGHT:
            self.vy *= -1


# The antibac class (splat, not the bottle)
class Antibac(Sprite):
    # Class initializer
    def __init__(self, x: int, y: int) -> None:
        # Initializes the parent class attributes
        super().__init__()

        # Load the image and construct the rect
        self.image: Surface = images["antibac"]
        self.mask: Mask = pg.mask.from_surface(self.image)
        self.rect: Rect = self.image.get_rect()
        self.rect.x: int = x
        self.rect.y: int = y


# The wall class
class Wall(Sprite):
    # Class initializer
    def __init__(self, x: int, y: int) -> None:
        # Initialize the parent class attributes
        super().__init__()

        # Load the image and construct the rect
        self.image: Surface = images["wall"]
        self.mask: Mask = pg.mask.from_surface(self.image)
        self.rect: Rect = self.image.get_rect()
        self.rect.x: int = x
        self.rect.y: int = y


# The bottle class
class Bottle(Sprite):
    # Class initializer
    def __init__(self, x: int, y: int) -> None:
        # Initialize the parent class attributes
        super().__init__()

        # Load the image and construct the rect
        self.image: Surface = images["bottle"]
        self.mask = pg.mask.from_surface(self.image)
        self.rect: Rect = self.image.get_rect()
        self.rect.x: int = x
        self.rect.y: int = y


# The exit class
class Exit(Sprite):
    # Class initializer
    def __init__(self, x: int, y: int) -> None:
        # Initialize the parent class attributes
        super().__init__()

        # Load the image and construct the rect
        self.image: Surface = images["exit"]
        self.mask: Mask = pg.mask.from_surface(self.image)
        self.rect: Rect = self.image.get_rect()
        self.rect.x: int = x
        self.rect.y: int = y


# ===========================================
# Game functions
# ===========================================


# Resets the level state and restarts
def restart(player: Player) -> None:
    # If the player instance does not have a valid 'rect' attribute, throw an error
    if not player.rect:
        raise RuntimeError("Player does not have a valid 'rect' attribute.")

    # Get the global variables
    global gameover, level_number, game_finished

    # Set the global variables
    gameover = False
    game_finished = False

    # Clear all the sprites
    virus_group.empty()
    antibac_group.empty()
    bottle_group.empty()
    wall_group.empty()
    exit_group.empty()
    player.reset()

    # Load the level objects from the level array if not finished
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

        # Generate the viruses ONLY if the game isn't finished
        for i in range(config.START_VIRUSES + level_number * config.VIRUSES_PER_LEVEL):
            # Ensure viruses don't spawn on top of the player or walls
            spawn_attempts = 0
            while spawn_attempts < 100:
                spawn_attempts += 1
                start_x: int = random.randint(0, config.WIDTH - config.SPRITE_SIZE)
                start_y: int = random.randint(0, config.HEIGHT - config.SPRITE_SIZE)

                # Temporary rect to check for overlap
                temp_rect = pg.Rect(
                    start_x, start_y, config.SPRITE_SIZE, config.SPRITE_SIZE
                )
                
                # Check for overlap with player or any wall
                if temp_rect.colliderect(player.rect):
                    continue
                
                if any(wall.rect.colliderect(temp_rect) for wall in wall_group if wall.rect):
                    continue
                    
                break
            
            # Skip this virus if a spawn position couldn't be found
            if spawn_attempts >= 100:
                continue

            # Randomize direction as well
            start_vx: int = random.randint(config.VIRUS_MIN_SPEED, config.VIRUS_MAX_SPEED)
            start_vy: int = random.randint(config.VIRUS_MIN_SPEED, config.VIRUS_MAX_SPEED)
            
            if random.random() < 0.5:
                start_vx *= -1
            if random.random() < 0.5:
                start_vy *= -1

            virus: Virus = Virus(start_x, start_y, start_vx, start_vy)
            virus_group.add(virus)

    # If level_number is equal to the level array length, the player has completed the game
    else:
        game_finished = True


# ===========================================
# Game initializaton
# ===========================================

# Render the text for the antibac count
count_text: Surface = font_30_b.render("Antibac: 0", True, colors.BLACK)
count_rect: Rect = count_text.get_rect()

# Position the antibac counter
count_rect.topright = (config.WIDTH - 10, 10)

# Keep track of the last time the counter was rendered so we won't need to re-render each frame
last_rendered: int = 0

# Initialize clock display variables
start_ticks: int = pg.time.get_ticks()
last_second: int = -1
clock_text: Surface = font_30_b.render("Time: 00:00", True, colors.BLACK)
clock_rect: Rect = clock_text.get_rect()
clock_rect.topleft = (10, 10)

# Create the player instance
player: Player = Player()
player_group.add(player)

# If the player rect was not properly created, throw an error
if not player.rect:
    raise RuntimeError("Failed to create 'rect' for player.")

# Restart once to initialize the game
restart(player)

# ===========================================
# Game loop
# ===========================================

# Keep the game running:
while is_running:
    # Get the keys pressed
    pressed: ScancodeWrapper = pg.key.get_pressed()

    # Set the player speed to 0
    player.vx = 0
    player.vy = 0

    # Handle keyboard input for movement
    if not (gameover or game_finished):
        if pressed[pg.K_w]:
            player.vy = -config.PLAYER_SPEED
        if pressed[pg.K_s]:
            player.vy = config.PLAYER_SPEED
        if pressed[pg.K_a]:
            player.vx = -config.PLAYER_SPEED
        if pressed[pg.K_d]:
            player.vx = config.PLAYER_SPEED

    # Check for collision with virus
    player_hit: dict[Sprite, list[Sprite]] = pg.sprite.groupcollide(
        player_group,
        virus_group,
        False,  # The player should not be removed on death
        False,  # Nor should the virus
        pg.sprite.collide_mask,  # ty: ignore
    )

    # If collision is detected, the player has lost
    if player_hit and not gameover and not player.is_invincible:
        gameover = True

    # Check for virus collision with antibac
    virus_hit: dict[Sprite, list[Sprite]] = pg.sprite.groupcollide(
        virus_group,
        antibac_group,
        True,  # The virus should be removed on contact
        True,  # So should the antibac
        pg.sprite.collide_mask,  # ty: ignore
    )

    # Update all the sprites
    virus_group.update()
    player_group.update()
    antibac_group.update()
    exit_group.update()

    # Start the drawing process
    screen.fill(config.BGCOLOR)
    virus_group.draw(screen)
    player_group.draw(screen)
    antibac_group.draw(screen)
    exit_group.draw(screen)
    bottle_group.draw(screen)
    wall_group.draw(screen)

    # Draw the held wall if there is one
    if held_wall := player.held_wall:
        # If the held wall does not have an image and a rect, throw an error
        if not (held_wall.image and held_wall.rect):
            raise RuntimeError(
                "Held wall does not have an 'image' and 'rect' attribute."
            )
        screen.blit(held_wall.image, held_wall.rect)

    # If the antibac count changed since last render, render again
    if player.antibac_count != last_rendered:
        # Update the flag
        last_rendered = player.antibac_count

        # Render the text for the antibac count
        count_text: Surface = font_30_b.render(
            f"Antibac: {player.antibac_count}", True, colors.BLACK
        )
        count_rect: Rect = count_text.get_rect()

        # Position the antibac counter
        count_rect.topright = (config.WIDTH - 10, 10)

    # Draw the current antibac count to the screen
    screen.blit(count_text, count_rect)

    # Calculate and display the elapsed time
    if not (gameover or game_finished):
        current_ticks: int = pg.time.get_ticks()
        seconds: int = (current_ticks - start_ticks) // 1000

        # Only re-render if the second changed
        if seconds != last_second:
            last_second = seconds
            minutes: int = seconds // 60
            rem_seconds: int = seconds % 60
            clock_text = font_30_b.render(
                f"Time: {minutes:02}:{rem_seconds:02}", True, colors.BLACK
            )
            clock_rect = clock_text.get_rect()
            clock_rect.topleft = (10, 10)

    # Draw the clock to the screen
    screen.blit(clock_text, clock_rect)

    # If the game is over, show the gameover text
    if gameover:
        screen.blit(gameover_text, gameover_rect)

    # Or if the player has won, show the victory text
    if game_finished:
        screen.blit(complete_text, complete_text_rect)

    # Tick the clock and update display
    clock.tick(config.TARGET_FPS)
    pg.display.update()

    # Handle events
    for event in pg.event.get():
        # If the window receives a 'quit' event, stop the game loop.
        if event.type == pg.QUIT:
            is_running = False

        # Runs if the player releases a key
        if event.type == pg.KEYUP:
            # If the key released is 'L', place antibac
            if event.key == pg.K_l:
                # Only runs if the player has a non-zero antibac count
                if player.antibac_count > 0 and not gameover:
                    antibac: Antibac = Antibac(int(player.rect.x), int(player.rect.y))
                    antibac_group.add(antibac)

                    # Decrement the antibac counter
                    player.antibac_count -= 1

            # If the player pressed 'K', pick up or drop a wall
            elif event.key == pg.K_k:
                # If carrying a wall, drop it
                if held_wall := player.held_wall:
                    # Ensure the held wall has a 'rect' attribute
                    if not held_wall.rect:
                        raise RuntimeError(
                            "Held wall does not have a valid 'rect' attribute."
                        )

                    # Check if the drop position is occupied by another wall OR the player
                    occupied = any(
                        wall.rect.colliderect(held_wall.rect)
                        for wall in wall_group
                        if wall.rect
                    ) or player.rect.colliderect(held_wall.rect)

                    if not occupied:
                        wall_group.add(player.held_wall)
                        player.held_wall = None

                # Otherwise, attempt to pick up a nearby wall
                elif not gameover:
                    # Search for walls exactly one grid square in front of the player
                    search_rect: Rect = cast(Rect, player.rect.copy())
                    search_rect.x = (player.rect.centerx // 32 + player.facing_x) * 32
                    search_rect.y = (player.rect.centery // 32 + player.facing_y) * 32

                    # Gather all the walls in the search area
                    nearby_walls: list[Wall] = [
                        cast(Wall, wall)
                        for wall in wall_group
                        if wall.rect and search_rect.colliderect(wall.rect)
                    ]

                    # Pick up the first wall found
                    if nearby_walls:
                        wall: Wall = nearby_walls[0]
                        wall_group.remove(wall)
                        player.held_wall = wall

            # If the player pressed 'N', start a new game
            elif event.key == pg.K_n:
                level_number = 0
                start_ticks = pg.time.get_ticks()
                last_second = -1
                restart(player)

            # If the player pressed 'F11', toggle fullscreen
            elif event.key == pg.K_F11:
                # Checks to see if the screen is currently fullscreen
                is_fullscreen: int = screen.get_flags() & pg.FULLSCREEN

                # Toggles the window size
                if is_fullscreen:
                    screen = pg.display.set_mode(config.DIMENSIONS, pg.SCALED)
                else:
                    screen = pg.display.set_mode(
                        config.DIMENSIONS, pg.SCALED | pg.FULLSCREEN
                    )

            # If the player pressed 'ESC', exit the game
            elif event.key == pg.K_ESCAPE:
                is_running = False

# Uninitialize pygame
pg.quit()
