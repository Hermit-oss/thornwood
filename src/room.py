# room.py

import os
import pygame
from src.wfc import WaveFunctionCollapse
from src.tilemap import TileMap
from src.util import TileJsonLoader
from src.spritesheet import Spritesheet
from src.object import Object
from src.enemy import Enemy
import random  # Import random module to create Random instances

DATA_PATH = os.path.join("assets", "data")
json_loader = TileJsonLoader(DATA_PATH)
TILESET = json_loader.load_json("tileset.json")
TILE_CONSTRAINTS = json_loader.load_json("tile_constraints.json")

ROOM_DIMENSIONS = (50, 50)  # Adjust room dimensions as needed
TILE_SIZE = 16

class Room:
    def __init__(self, position, base_seed=0, is_goal_room=False, is_spawn_room=False):
        self.position = position  # Tuple of (x, y)
        self.base_seed = base_seed
        self.is_goal_room = is_goal_room
        self.is_spawn_room = is_spawn_room

        # Generate a unique seed for this room based on base seed and room position
        self.room_seed = (self.base_seed * 73856093 + self.position[0] * 19349663 + self.position[1] * 83492791) % (2**32)

        self.tile_map = self.generate_tile_map()
        self.objects = []
        self.enemies = []
        self.generate_objects()
        if not self.is_spawn_room:
            self.generate_enemies()
        if self.is_goal_room:
            self.create_goal_object()

    def generate_tile_map(self):
        # Use the room's seed for the tile map
        wfc = WaveFunctionCollapse(ROOM_DIMENSIONS, TILESET, TILE_CONSTRAINTS, random_seed=self.room_seed)
        wfc.collapse()
        collapsed_map = wfc.get_collapsed_grid()

        # Generate the TileMap for this room
        spritesheet = Spritesheet(os.path.join('assets', 'tileset', 'tileset.png'))
        tile_map = TileMap(collapsed_map, spritesheet)
        return tile_map

    def generate_objects(self):
        """
        Generates objects in the room on tiles that are marked as generatable.
        """
        # Create a local random generator for objects
        object_seed = (self.room_seed * 31 + 1) % (2**32)
        rand_gen = random.Random(object_seed)

        # Iterate over tiles in the tile_map
        for y, row in enumerate(self.tile_map.tile_map):
            for x, tile in enumerate(row):
                tile_info = self.tile_map.TILESET.get(tile.tile_type, {})
                if tile_info.get('generatable', False):
                    # Decide whether to generate an object here
                    chance = 0.1  # 10% chance to generate an object (adjust as needed)
                    if rand_gen.random() < chance:
                        # Randomly choose an object type (e.g., "rock1" or "rock2")
                        object_type = rand_gen.choice(['rock1', 'rock2'])
                        # Create an object and add it to the objects list
                        obj = Object(x, y, object_type, spritesheet=self.tile_map.spritesheet)
                        self.objects.append(obj)
                        # Add the object's rect to collidable tiles for collision detection
                        self.tile_map.collidable_tiles.append(obj)

    def create_goal_object(self):
        """
        Places the flower object on a random 'grass_plain' or 'grass_small' tile in the room.
        """
        # Create a local random generator for the goal object
        goal_seed = (self.room_seed * 37 + 2) % (2**32)
        rand_gen = random.Random(goal_seed)

        # Find all tiles that are 'grass_plain' or 'grass_small'
        suitable_tiles = []
        for y, row in enumerate(self.tile_map.tile_map):
            for x, tile in enumerate(row):
                if tile.tile_type in ['grass_plain', 'grass_small']:
                    # Check if there is already an object here
                    object_here = any(obj.pos_x == x and obj.pos_y == y for obj in self.objects)
                    if not object_here:
                        suitable_tiles.append((x, y))

        if suitable_tiles:
            # Randomly select one of the suitable tiles
            flower_x, flower_y = rand_gen.choice(suitable_tiles)
            # Create the flower object
            flower_obj = Object(flower_x, flower_y, 'flower', spritesheet=self.tile_map.spritesheet)
            self.objects.append(flower_obj)
            # The flower is not collidable, so we don't add it to collidable_tiles
        else:
            # If no suitable tile is found, log a warning (optional)
            print(f"No suitable tile found for goal object in room {self.position}")

    def generate_enemies(self):
        """
        Generates enemies in the room.
        """
        # Create a local random generator for enemies
        enemy_seed = (self.room_seed * 41 + 3) % (2**32)
        rand_gen = random.Random(enemy_seed)

        # Decide whether to spawn enemies in this room
        spawn_chance = 0.5  # 50% chance to spawn enemies
        if rand_gen.random() < spawn_chance:
            num_enemies = rand_gen.randint(1, 4)  # Spawn between 1 and 4 enemies

            # Find suitable spawn positions
            suitable_tiles = []
            for y, row in enumerate(self.tile_map.tile_map):
                for x, tile in enumerate(row):
                    if not tile.collidable:
                        # Check for objects or enemies at this position
                        occupied = any(obj.pos_x == x and obj.pos_y == y for obj in self.objects)
                        occupied |= any(
                            int(enemy.position.x) // TILE_SIZE == x and int(enemy.position.y) // TILE_SIZE == y
                            for enemy in self.enemies
                        )
                        if not occupied:
                            suitable_tiles.append((x, y))

            # Spawn enemies at random suitable positions
            spritesheet = self.tile_map.spritesheet
            for _ in range(num_enemies):
                if suitable_tiles:
                    spawn_pos = rand_gen.choice(suitable_tiles)
                    x, y = spawn_pos
                    enemy = Enemy(spritesheet, (x * TILE_SIZE, y * TILE_SIZE))
                    self.enemies.append(enemy)
                    suitable_tiles.remove(spawn_pos)
                else:
                    break  # No more suitable positions

    def draw_objects(self, surface, camera):
        for obj in self.objects:
            obj.draw(surface, camera)

    def draw_enemies(self, surface, camera):
        for enemy in self.enemies:
            enemy.draw(surface, camera)
