import pygame
import os
from src.camera import Camera
from src.util import TileJsonLoader

# Load configuration data
DATA_PATH = os.path.join("assets", "data")
json_loader = TileJsonLoader(DATA_PATH)
TILESET = json_loader.load_json("tileset.json")
TILE_CONSTRAINTS = json_loader.load_json("tile_constraints.json")
DIRECTIONS = json_loader.load_json("directions.json")
REVERSE_DIRECTIONS = json_loader.load_json("reverse_directions.json")
CHARACTER_TILESET = json_loader.load_json("character_tileset.json")

TILE_SIZE = 16

class Character:
    """
    Represents the player character in the game.

    Manages the character's movement, animations, interactions, health, and collision detection.
    """

    def __init__(self, spritesheet, position, world_width, world_height):
        """
        Initializes the Character object.

        Args:
            spritesheet (Spritesheet): The spritesheet containing character images.
            position (tuple): The initial (x, y) position of the character in pixels.
            world_width (int): The width of the current game world (room) in pixels.
            world_height (int): The height of the current game world (room) in pixels.
        """
        self.spritesheet = spritesheet
        self.position = pygame.Vector2(position)
        self.world_width = world_width
        self.world_height = world_height
        self.animation_speed = 0.25  # Time between animation frames in seconds

        # Load character animation frames from the tileset
        self.animations = {
            direction: [
                self.spritesheet.get_image(x, y, TILE_SIZE, TILE_SIZE)
                for x, y in CHARACTER_TILESET[f"char_{direction}"]
            ]
            for direction in ['down', 'left', 'right', 'up']
        }

        # Define idle frames for each direction
        self.idle_frames = {
            direction: self.spritesheet.get_image(1, index, TILE_SIZE, TILE_SIZE)
            for index, direction in enumerate(['down', 'left', 'right', 'up'])
        }

        self.current_animation = 'down'
        self.facing_direction = 'down'
        self.frame_index = 0
        self.image = self.animations[self.current_animation][self.frame_index]
        self.animation_timer = 0

        # Define a smaller collision rectangle for precise collision detection
        collision_rect_size = 10  # Adjust the size as needed
        self.collision_rect_offset = (
            (TILE_SIZE - collision_rect_size) // 2,
            (TILE_SIZE - collision_rect_size) // 2
        )
        self.collision_rect = pygame.Rect(
            self.position.x + self.collision_rect_offset[0],
            self.position.y + self.collision_rect_offset[1],
            collision_rect_size,
            collision_rect_size
        )

        # Define the rect for drawing and camera purposes
        self.rect = self.image.get_rect(topleft=self.position)

        # Initialize interaction rectangle for object interactions
        self.interaction_rect = pygame.Rect(0, 0, collision_rect_size, collision_rect_size)
        self.update_interaction_rect()

        self.max_health = 5.0
        self.health = self.max_health

        # Invincibility frames after taking damage
        self.invincible_time = 0
        self.I_FRAMES_DURATION = 0.5  # Duration of invincibility in seconds

        # Enemy interaction rectangle for attacking enemies
        self.enemy_interaction_rect = pygame.Rect(0, 0, 40, 40)
        self.update_enemy_interaction_rect()

    def update(self, dt):
        """
        Updates the character's state each frame.

        Args:
            dt (float): Delta time since the last frame in seconds.
        """
        # Update invincibility timer
        if self.invincible_time > 0:
            self.invincible_time = max(0, self.invincible_time - dt)

    def take_damage(self, amount):
        """
        Reduces the character's health by the specified amount if not invincible.

        Args:
            amount (float): The amount of damage to take.
        """
        if self.invincible_time <= 0:
            self.health = max(0, self.health - amount)
            self.invincible_time = self.I_FRAMES_DURATION

    def restore_health(self, amount):
        """
        Restores the character's health by the specified amount.

        Args:
            amount (float): The amount of health to restore.
        """
        self.health = min(self.max_health, self.health + amount)

    def update_enemy_interaction_rect(self):
        """
        Updates the position of the enemy interaction rectangle based on the facing direction.
        """
        interaction_offset = 10  # Distance in pixels in front of the character
        size = 40  # Size of the enemy interaction rectangle

        if self.facing_direction == 'up':
            self.enemy_interaction_rect.size = (size, size)
            self.enemy_interaction_rect.centerx = self.position.x + TILE_SIZE // 2
            self.enemy_interaction_rect.bottom = self.position.y - interaction_offset
        elif self.facing_direction == 'down':
            self.enemy_interaction_rect.size = (size, size)
            self.enemy_interaction_rect.centerx = self.position.x + TILE_SIZE // 2
            self.enemy_interaction_rect.top = self.position.y + TILE_SIZE + interaction_offset
        elif self.facing_direction == 'left':
            self.enemy_interaction_rect.size = (size, size)
            self.enemy_interaction_rect.right = self.position.x - interaction_offset
            self.enemy_interaction_rect.centery = self.position.y + TILE_SIZE // 2
        elif self.facing_direction == 'right':
            self.enemy_interaction_rect.size = (size, size)
            self.enemy_interaction_rect.left = self.position.x + TILE_SIZE + interaction_offset
            self.enemy_interaction_rect.centery = self.position.y + TILE_SIZE // 2

    def move(self, dx, dy, dt, tile_map):
        """
        Moves the character based on input and handles collisions.

        Args:
            dx (float): Movement direction along the x-axis (-1, 0, or 1).
            dy (float): Movement direction along the y-axis (-1, 0, or 1).
            dt (float): Delta time since the last frame in seconds.
            tile_map (TileMap): The current tile map for collision detection.
        """
        speed = 100  # Movement speed in pixels per second
        delta_x = dx * speed * dt
        delta_y = dy * speed * dt

        original_position = self.position.copy()

        # Attempt to move in both axes
        self.position.x += delta_x
        self.position.y += delta_y
        self.update_collision_rect()

        if self.check_collision(self.collision_rect, tile_map.collidable_tiles):
            # Collision detected; revert to original position
            self.position = original_position.copy()
            self.update_collision_rect()

            # Attempt to move only along the x-axis
            self.position.x += delta_x
            self.update_collision_rect()
            if self.check_collision(self.collision_rect, tile_map.collidable_tiles):
                self.position.x -= delta_x  # Revert x movement
                self.update_collision_rect()

            # Attempt to move only along the y-axis
            self.position.y += delta_y
            self.update_collision_rect()
            if self.check_collision(self.collision_rect, tile_map.collidable_tiles):
                self.position.y -= delta_y  # Revert y movement
                self.update_collision_rect()

        # Update facing direction and animation based on movement
        if dx > 0:
            self.current_animation = 'right'
            self.facing_direction = 'right'
        elif dx < 0:
            self.current_animation = 'left'
            self.facing_direction = 'left'
        elif dy > 0:
            self.current_animation = 'down'
            self.facing_direction = 'down'
        elif dy < 0:
            self.current_animation = 'up'
            self.facing_direction = 'up'

        # Update interaction rectangles
        self.update_interaction_rect()
        self.update_enemy_interaction_rect()

        # Update animation
        if dx != 0 or dy != 0:
            self.update_animation(dt)
        else:
            # When not moving, set the image to the idle frame
            self.image = self.idle_frames[self.facing_direction]
            self.frame_index = 0
            self.animation_timer = 0

        # Check for room transition
        self.room_transition_direction = None
        if self.position.x < 0:
            self.room_transition_direction = 'left'
        elif self.position.x > self.world_width - TILE_SIZE:
            self.room_transition_direction = 'right'
        elif self.position.y < 0:
            self.room_transition_direction = 'up'
        elif self.position.y > self.world_height - TILE_SIZE:
            self.room_transition_direction = 'down'

        # Keep the character within the world boundaries
        self.position.x = max(0, min(self.position.x, self.world_width - TILE_SIZE))
        self.position.y = max(0, min(self.position.y, self.world_height - TILE_SIZE))
        self.update_collision_rect()

    def update_interaction_rect(self):
        """
        Updates the position of the object interaction rectangle based on the facing direction.
        """
        interaction_offset = 5  # Distance in pixels in front of the character
        size = 10  # Size of the interaction rectangle

        if self.facing_direction == 'up':
            self.interaction_rect.size = (size, size)
            self.interaction_rect.centerx = self.position.x + TILE_SIZE // 2
            self.interaction_rect.bottom = (
                self.position.y + self.collision_rect_offset[1] - interaction_offset
            )
        elif self.facing_direction == 'down':
            self.interaction_rect.size = (size, size)
            self.interaction_rect.centerx = self.position.x + TILE_SIZE // 2
            self.interaction_rect.top = (
                self.position.y + TILE_SIZE - self.collision_rect_offset[1] + interaction_offset
            )
        elif self.facing_direction == 'left':
            self.interaction_rect.size = (size, size)
            self.interaction_rect.right = (
                self.position.x + self.collision_rect_offset[0] - interaction_offset
            )
            self.interaction_rect.centery = self.position.y + TILE_SIZE // 2
        elif self.facing_direction == 'right':
            self.interaction_rect.size = (size, size)
            self.interaction_rect.left = (
                self.position.x + TILE_SIZE - self.collision_rect_offset[0] + interaction_offset
            )
            self.interaction_rect.centery = self.position.y + TILE_SIZE // 2

    def update_collision_rect(self):
        """
        Updates the positions of collision and drawing rectangles based on the character's position.
        """
        self.collision_rect.topleft = (
            self.position.x + self.collision_rect_offset[0],
            self.position.y + self.collision_rect_offset[1]
        )
        self.rect.topleft = self.position

    def check_collision(self, rect, collidable_tiles):
        """
        Checks for collisions between the character and collidable tiles.

        Args:
            rect (pygame.Rect): The rectangle to check for collisions.
            collidable_tiles (List[Tile]): A list of tiles that are collidable.

        Returns:
            bool: True if a collision is detected; False otherwise.
        """
        return any(rect.colliderect(tile.rect) for tile in collidable_tiles)

    def update_animation(self, dt):
        """
        Updates the character's animation frames based on the animation timer.

        Args:
            dt (float): Delta time since the last frame in seconds.
        """
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.frame_index = (self.frame_index + 1) % len(self.animations[self.current_animation])
            self.image = self.animations[self.current_animation][self.frame_index]

    def draw_health_bar(self, surface):
        """
        Draws the character's health bar on the screen.

        Args:
            surface (pygame.Surface): The surface to draw the health bar on.
        """
        bar_width = 100
        bar_height = 10
        x = 10  # Horizontal position on the screen
        y = 10  # Vertical position on the screen
        health_ratio = self.health / self.max_health
        pygame.draw.rect(surface, (255, 0, 0), (x, y, bar_width, bar_height))  # Background bar
        pygame.draw.rect(
            surface,
            (0, 255, 0),
            (x, y, bar_width * health_ratio, bar_height)
        )  # Health bar

    def draw(self, screen, camera):
        """
        Draws the character and optional debug rectangles on the screen.

        Args:
            screen (pygame.Surface): The game screen to draw on.
            camera (Camera): The camera object for adjusting the drawing position.
        """
        # Adjust for the camera offset and draw the character
        screen.blit(
            self.image,
            (self.position.x - camera.x, self.position.y - camera.y)
        )

        # Optional: Draw the interaction rectangles for debugging
        # Uncomment the lines below to visualize interaction areas

        # Object interaction rectangle (green)
        # debug_rect = self.interaction_rect.move(-camera.x, -camera.y)
        # pygame.draw.rect(screen, (0, 255, 0), debug_rect, 1)

        # Enemy interaction rectangle (red)
        # debug_enemy_rect = self.enemy_interaction_rect.move(-camera.x, -camera.y)
        # pygame.draw.rect(screen, (255, 0, 0), debug_enemy_rect, 1)