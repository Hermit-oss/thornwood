import pygame
import heapq  # For priority queue in A* algorithm
from src.spritesheet import Spritesheet
from src.tile import TILE_SIZE
from src.character import CHARACTER_TILESET

class Enemy:
    """
    Represents an enemy character in the game.

    The enemy can navigate the game world using pathfinding to chase the player,
    handle animations, and manage collisions with the environment.
    """

    def __init__(self, spritesheet, position, tile_size=TILE_SIZE):
        """
        Initializes the Enemy object.

        Args:
            spritesheet (Spritesheet): The spritesheet containing enemy images.
            position (tuple): The initial (x, y) position of the enemy in pixels.
            tile_size (int): The size of the tiles in pixels.
        """
        self.spritesheet = spritesheet
        self.position = pygame.Vector2(position)
        self.tile_size = tile_size
        self.speed = 70  # Movement speed in pixels per second
        self.animation_speed = 0.1  # Time between animation frames in seconds

        # Load enemy animation frames by applying a color shift to the character frames
        self.animations = {
            direction: [
                self.color_shift(
                    self.spritesheet.get_image(x, y, tile_size, tile_size),
                    (255, 0, 0)
                )
                for x, y in CHARACTER_TILESET[f'char_{direction}']
            ]
            for direction in ['down', 'left', 'right', 'up']
        }

        # Define idle frames for each direction
        idle_positions = {
            'down': (1, 0),
            'left': (1, 1),
            'right': (1, 2),
            'up': (1, 3)
        }
        self.idle_frames = {
            direction: self.color_shift(
                self.spritesheet.get_image(pos[0], pos[1], tile_size, tile_size),
                (255, 0, 0)
            )
            for direction, pos in idle_positions.items()
        }

        self.current_animation = 'down'
        self.facing_direction = 'down'
        self.frame_index = 0
        self.image = self.animations[self.current_animation][self.frame_index]
        self.animation_timer = 0

        # Collision rectangle for the enemy
        self.collision_rect = self.image.get_rect(topleft=self.position)

        # Pathfinding attributes
        self.path = []  # List of (x, y) tile coordinates representing the path
        self.path_step = 0  # Current step in the path

    def color_shift(self, image, color):
        """
        Applies a color shift to the given image.

        Args:
            image (pygame.Surface): The original image surface.
            color (tuple): The RGB color tuple to apply.

        Returns:
            pygame.Surface: The color-shifted image.
        """
        image = image.copy()
        color_image = pygame.Surface(image.get_size()).convert_alpha()
        color_image.fill(color)
        image.blit(color_image, (0, 0), special_flags=pygame.BLEND_MULT)
        return image

    def update(self, dt, player, tile_map):
        """
        Updates the enemy's state each frame.

        Args:
            dt (float): Delta time since the last frame in seconds.
            player (Character): The player character to chase.
            tile_map (TileMap): The current tile map for collision detection and pathfinding.
        """
        # Recalculate path to the player's current position
        self.calculate_path(player, tile_map)

        if self.path and self.path_step < len(self.path):
            # Move along the path
            target_pos = pygame.Vector2(self.path[self.path_step]) * self.tile_size
            direction_vector = target_pos - self.position

            if direction_vector.length() > 0:
                distance = self.speed * dt
                if direction_vector.length() <= distance:
                    # Move directly to the target position and advance to the next step
                    self.position = target_pos
                    self.path_step += 1
                else:
                    # Move towards the target position
                    direction_vector = direction_vector.normalize()
                    delta = direction_vector * distance
                    self.move(delta.x, delta.y, tile_map)
            else:
                self.path_step += 1

            if self.path_step >= len(self.path):
                # Reached the end of the path
                self.path = []
                self.path_step = 0

            # Update facing direction based on movement
            dx = target_pos.x - self.position.x
            dy = target_pos.y - self.position.y
            self.update_facing_direction(dx, dy)

            # Update animation
            self.update_animation(dt)
        else:
            # No path found or path completed; move directly towards the player
            direction_vector = player.position - self.position
            if direction_vector.length() > 0:
                direction_vector = direction_vector.normalize()
                delta = direction_vector * self.speed * dt
                self.move(delta.x, delta.y, tile_map)

                # Update facing direction based on movement
                dx = player.position.x - self.position.x
                dy = player.position.y - self.position.y
                self.update_facing_direction(dx, dy)

                # Update animation
                self.update_animation(dt)
            else:
                # Enemy has reached the player; use idle frame
                self.image = self.idle_frames[self.facing_direction]
                self.frame_index = 0
                self.animation_timer = 0

        # Update collision rect position
        self.collision_rect.topleft = self.position

    def move(self, dx, dy, tile_map):
        """
        Moves the enemy by the specified amounts, handling collisions.

        Args:
            dx (float): Amount to move along the x-axis.
            dy (float): Amount to move along the y-axis.
            tile_map (TileMap): The current tile map for collision detection.
        """
        original_position = self.position.copy()

        # Attempt to move along the x-axis
        self.position.x += dx
        self.collision_rect.topleft = self.position
        if self.check_collision(self.collision_rect, tile_map.collidable_tiles):
            self.position.x = original_position.x

        # Attempt to move along the y-axis
        self.position.y += dy
        self.collision_rect.topleft = self.position
        if self.check_collision(self.collision_rect, tile_map.collidable_tiles):
            self.position.y = original_position.y

        self.collision_rect.topleft = self.position

    def check_collision(self, rect, collidable_tiles):
        """
        Checks for collisions between the enemy and collidable tiles.

        Args:
            rect (pygame.Rect): The rectangle to check for collisions.
            collidable_tiles (List[Tile]): A list of tiles that are collidable.

        Returns:
            bool: True if a collision is detected; False otherwise.
        """
        return any(rect.colliderect(tile.rect) for tile in collidable_tiles)

    def update_animation(self, dt):
        """
        Updates the enemy's animation frames based on the animation timer.

        Args:
            dt (float): Delta time since the last frame in seconds.
        """
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.frame_index = (self.frame_index + 1) % len(self.animations[self.current_animation])
            self.image = self.animations[self.current_animation][self.frame_index]

    def update_facing_direction(self, dx, dy):
        """
        Updates the enemy's facing direction based on movement deltas.

        Args:
            dx (float): Change in position along the x-axis.
            dy (float): Change in position along the y-axis.
        """
        if abs(dx) > abs(dy):
            if dx > 0:
                self.current_animation = 'right'
                self.facing_direction = 'right'
            else:
                self.current_animation = 'left'
                self.facing_direction = 'left'
        else:
            if dy > 0:
                self.current_animation = 'down'
                self.facing_direction = 'down'
            else:
                self.current_animation = 'up'
                self.facing_direction = 'up'

    def draw(self, screen, camera):
        """
        Draws the enemy on the screen, adjusted for the camera position.

        Args:
            screen (pygame.Surface): The game screen to draw on.
            camera (Camera): The camera object for adjusting the drawing position.
        """
        screen.blit(self.image, (self.position.x - camera.x, self.position.y - camera.y))

    def calculate_path(self, player, tile_map):
        """
        Calculates a path to the player's current position using A* pathfinding.

        Args:
            player (Character): The player character to chase.
            tile_map (TileMap): The current tile map for collision detection and pathfinding.
        """
        start = (int(self.position.x // self.tile_size), int(self.position.y // self.tile_size))
        player_tile = (int(player.position.x // self.tile_size), int(player.position.y // self.tile_size))

        width = tile_map.width
        height = tile_map.height

        # Create a set of collidable positions (tiles and objects)
        collidable_positions = {
            (int(tile.rect.x // self.tile_size), int(tile.rect.y // self.tile_size))
            for tile in tile_map.collidable_tiles
        }

        # List of potential goals (player's tile and adjacent accessible tiles)
        potential_goals = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # 4-way connectivity

        # Include player's tile if it's not collidable
        if player_tile not in collidable_positions:
            potential_goals.append(player_tile)

        # Check adjacent tiles around the player
        for dx, dy in directions:
            nx, ny = player_tile[0] + dx, player_tile[1] + dy
            if 0 <= nx < width and 0 <= ny < height:
                if (nx, ny) not in collidable_positions:
                    potential_goals.append((nx, ny))

        # Remove duplicates while preserving order
        potential_goals = list(dict.fromkeys(potential_goals))

        # Attempt to find a path to one of the potential goals
        path_found = False
        for goal in potential_goals:
            path = self.a_star_search(start, goal, collidable_positions, width, height)
            if path:
                self.path = path
                self.path_step = 0  # Start from the first tile in the path
                path_found = True
                break  # Stop after finding the first valid path

        if not path_found:
            # No path found; clear the path
            self.path = []
            self.path_step = 0

    def a_star_search(self, start, goal, collidable_positions, width, height):
        """
        Performs A* pathfinding to find a path from start to goal.

        Args:
            start (tuple): The starting tile coordinate (x, y).
            goal (tuple): The goal tile coordinate (x, y).
            collidable_positions (set): Set of tile coordinates that are collidable.
            width (int): Width of the tile map in tiles.
            height (int): Height of the tile map in tiles.

        Returns:
            list: A list of tile coordinates representing the path, or None if no path is found.
        """
        def heuristic(a, b):
            # Manhattan distance heuristic
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        f_score = {start: heuristic(start, goal)}
        closed_set = set()

        while open_set:
            current = heapq.heappop(open_set)[1]
            if current == goal:
                # Reconstruct path from goal to start
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                return path

            closed_set.add(current)

            for neighbor in self.get_neighbors(current, width, height, collidable_positions):
                if neighbor in closed_set:
                    continue
                tentative_g_score = g_score[current] + 1  # Cost between nodes is assumed to be 1
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

        # No path found
        return None

    def get_neighbors(self, node, width, height, collidable_positions):
        """
        Retrieves accessible neighboring tiles for pathfinding.

        Args:
            node (tuple): The current tile coordinate (x, y).
            width (int): Width of the tile map in tiles.
            height (int): Height of the tile map in tiles.
            collidable_positions (set): Set of tile coordinates that are collidable.

        Returns:
            list: A list of accessible neighboring tile coordinates.
        """
        x, y = node
        neighbors = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # 4-way connectivity

        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height:
                if (nx, ny) not in collidable_positions:
                    neighbors.append((nx, ny))
        return neighbors