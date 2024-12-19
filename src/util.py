import json
import os

class TileJsonLoader:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.tileset = {}
        self.tile_constraints = {}
        self.directions = {}
        self.reverse_directions = {}
        self.character_tileset = {}

    def load_json(self, file_name):
        file_path = os.path.join(self.data_dir, file_name)
        with open(file_path, 'r') as file:
            return json.load(file)

    def load_tileset(self):
        self.tileset = self.load_json("tileset.json")

    def load_tile_constraints(self):
        self.tile_constraints = self.load_json("tile_constraints.json")

    def load_directions(self):
        self.directions = self.load_json("directions.json")

    def load_reverse_directions(self):
        self.reverse_directions = self.load_json("reverse_directions.json")

    def load_character_tileset(self):
        self.character_tileset = self.load_json("character_tileset.json")

    def load_all(self):
        self.load_tileset()
        self.load_tile_constraints()
        self.load_directions()
        self.load_reverse_directions()
        self.load_character_tileset()