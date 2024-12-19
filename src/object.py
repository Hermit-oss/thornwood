import pygame
import os
from src.spritesheet import Spritesheet
from src.tile import TILE_SIZE
from src.util import TileJsonLoader

DATA_PATH = os.path.join("assets", "data")
json_loader = TileJsonLoader(DATA_PATH)
TILESET = json_loader.load_json("tileset.json")

class Object:
    def __init__(self, pos_x, pos_y, object_type, tile_size=TILE_SIZE, spritesheet=None):
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.object_type = object_type
        self.tile_size = tile_size
        self.collidable = True  # Rocks are collidable by default

        if object_type in TILESET:
            tile_info = TILESET[object_type]
            tile_coords = tile_info['position']
            self.image = spritesheet.get_image(tile_coords[0], tile_coords[1], tile_size, tile_size)
        else:
            # Fallback image for unknown object types
            self.image = pygame.Surface((tile_size, tile_size))
            self.image.fill((255, 0, 255))  # Magenta color for missing texture

        self.rect = pygame.Rect(
            self.pos_x * self.tile_size,
            self.pos_y * self.tile_size,
            self.tile_size,
            self.tile_size
        )

    def draw(self, surface, camera):
        screen_x = self.pos_x * self.tile_size - camera.x
        screen_y = self.pos_y * self.tile_size - camera.y
        surface.blit(self.image, (screen_x, screen_y))
