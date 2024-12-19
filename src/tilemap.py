from src.tile import Tile
from src.spritesheet import Spritesheet
from src.camera import Camera
from src.util import TileJsonLoader
import os

DATA_PATH = os.path.join("assets", "data")
json_loader = TileJsonLoader(DATA_PATH)
TILESET = json_loader.load_json("tileset.json")
TILE_CONSTRAINTS = json_loader.load_json("tile_constraints.json")
DIRECTIONS = json_loader.load_json("directions.json")
REVERSE_DIRECTIONS = json_loader.load_json("reverse_directions.json")
CHARACTER_TILESET = json_loader.load_json("character_tileset.json")

TILE_SIZE = 16

class TileMap:
    def __init__(self, tile_names, spritesheet, tile_size=TILE_SIZE):
        self.tile_map = []
        self.collidable_tiles = []  # List to hold collidable tiles
        self.width = len(tile_names[0]) if tile_names else 0
        self.height = len(tile_names)
        self.tile_size = tile_size
        self.spritesheet = spritesheet

        # Load TILESET
        self.TILESET = json_loader.load_json("tileset.json")

        for y, row in enumerate(tile_names):
            tile_row = []
            for x, tile_name in enumerate(row):
                if tile_name in self.TILESET:
                    tile_info = self.TILESET[tile_name]
                    tile_coords = tile_info['position']
                    image = spritesheet.get_image(tile_coords[0], tile_coords[1], tile_size, tile_size)
                    collidable = tile_info.get('collidable', False)  # Get collidable property
                else:
                    # Fallback image for unknown tile types
                    image = spritesheet.get_image(10, 1, tile_size, tile_size)
                    collidable = False

                tile = Tile(x, y, tile_name, tile_size, image, collidable)
                tile_row.append(tile)
                if collidable:
                    self.collidable_tiles.append(tile)  # Add to collidable tiles list
            self.tile_map.append(tile_row)

    def draw(self, surface, camera):
        # Only draw the tiles visible within the camera
        for row in self.tile_map:
            for tile in row:
                tile.draw(surface, camera)