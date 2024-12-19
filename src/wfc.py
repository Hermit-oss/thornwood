# wfc.py
from src.cell import Cell
from src.util import TileJsonLoader
import random
import os
from collections import OrderedDict

DATA_PATH = os.path.join("assets", "data")
json_loader = TileJsonLoader(DATA_PATH)
TILESET = json_loader.load_json("tileset.json")
TILE_CONSTRAINTS = json_loader.load_json("tile_constraints.json")
DIRECTIONS = json_loader.load_json("directions.json")
REVERSE_DIRECTIONS = json_loader.load_json("reverse_directions.json")
CHARACTER_TILESET = json_loader.load_json("character_tileset.json")

# Convert to OrderedDict to maintain consistent ordering
TILESET = OrderedDict(sorted(TILESET.items()))
TILE_CONSTRAINTS = OrderedDict(sorted(TILE_CONSTRAINTS.items()))

class WaveFunctionCollapse:
    def __init__(self, grid_size, tileset, tile_constraints, seed=None, random_seed=None):
        self.width, self.height = grid_size
        self.tileset = tileset
        self.tile_constraints = tile_constraints
        self.seed = seed
        self.random_seed = random_seed
        self.random_gen = random.Random(random_seed)  # Initialize deterministic random generator

        # Initialize grid with all possible tiles in each cell
        self.grid = [[Cell(x, y, tileset) for x in range(self.width)] for y in range(self.height)]

        # Apply initial seed if provided
        if seed:
            self.apply_seed(seed)

    def apply_seed(self, seed):
        # Deterministically apply the initial seed configuration
        for (x, y), tile_name in seed.items():
            cell = self.grid[y][x]
            if tile_name not in self.tileset:
                raise ValueError(f"Tile '{tile_name}' not in tileset.")
            cell.possible_tiles = {tile_name}
            cell.collapsed = True
            cell.tile = tile_name
            cell.entropy = 0
            success = self.propagate_constraints(cell, [])
            if not success:
                raise Exception("Conflict occurred during seed propagation.")

    def collapse(self):
        # Initialize the stack for backtracking
        stack = []

        while True:
            # Find the cell with the lowest non-zero entropy (excluding collapsed cells)
            cells = [cell for row in self.grid for cell in row if not cell.collapsed]
            if not cells:
                # All cells are collapsed
                break

            # Get minimum entropy cells
            min_entropy = min(cell.entropy for cell in cells)
            min_entropy_cells = [cell for cell in cells if cell.entropy == min_entropy]
            # Sort the cells to ensure consistent ordering
            min_entropy_cells.sort(key=lambda c: (c.y, c.x))  # Or any other consistent attribute

            # Select a cell deterministically using the seeded random generator
            cell = self.random_gen.choice(min_entropy_cells)

            # Select a tile based on weights
            tile_name = self.select_tile(cell)
            if tile_name is None:
                # Need to backtrack
                if not stack:
                    raise Exception("Failed to collapse the grid, no solution possible")
                else:
                    last_action_stack = stack.pop()
                    self.undo_actions(last_action_stack)
                    continue

            # Save the current state changes for backtracking
            action_stack = []

            # Record the change in the cell
            action_stack.append((cell, cell.possible_tiles.copy(), cell.collapsed, cell.tile, cell.entropy))

            # Collapse the cell
            cell.possible_tiles = [tile_name]
            cell.collapsed = True
            cell.tile = tile_name
            cell.entropy = 0

            # Propagate constraints deterministically
            success = self.propagate_constraints(cell, action_stack)

            if success:
                # Push the action stack onto the main stack
                stack.append(action_stack)
            else:
                # Conflict occurred, undo the actions
                self.undo_actions(action_stack)
                # Remove the chosen tile from the cell's possible tiles
                if tile_name in cell.possible_tiles:
                    cell.possible_tiles.remove(tile_name)
                cell.collapsed = False
                cell.tile = None
                cell.entropy = cell.calculate_entropy(self.tileset)

                if not cell.possible_tiles:
                    # Need to backtrack further
                    if not stack:
                        raise Exception("Failed to collapse the grid, no solution possible")
                    else:
                        last_action_stack = stack.pop()
                        self.undo_actions(last_action_stack)
                        continue

    def select_tile(self, cell):
        # Tiles are already sorted in cell.possible_tiles
        tiles = cell.possible_tiles
        weights = [self.tileset[tile]['weight'] for tile in tiles]
        if not weights:
            return None
        total_weight = sum(weights)
        probabilities = [w / total_weight for w in weights]
        tile_name = self.random_gen.choices(tiles, probabilities)[0]
        return tile_name

    def propagate_constraints(self, cell, action_stack):
        queue = [cell]
        while queue:
            # Sort the queue to ensure consistent processing order
            queue.sort(key=lambda c: (c.y, c.x))
            current_cell = queue.pop(0)
            x, y = current_cell.x, current_cell.y
            for direction in sorted(DIRECTIONS.keys()):
                dx, dy = DIRECTIONS[direction]
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    neighbor = self.grid[ny][nx]
                    if neighbor.collapsed:
                        continue
                    neighbor_possible_tiles = neighbor.possible_tiles.copy()
                    new_possible_tiles = []
                    reverse_direction = REVERSE_DIRECTIONS[direction]
                    for neighbor_tile in neighbor_possible_tiles:
                        compatible = False
                        allowed_tiles = self.tile_constraints.get(neighbor_tile, {}).get(reverse_direction, {})
                        for current_tile in current_cell.possible_tiles:
                            preference = allowed_tiles.get(current_tile, 0)
                            if preference > 0:
                                compatible = True
                                break
                        if compatible:
                            new_possible_tiles.append(neighbor_tile)
                    # Remove duplicates and sort
                    new_possible_tiles = sorted(set(new_possible_tiles))
                    if new_possible_tiles != neighbor.possible_tiles:
                        if not new_possible_tiles:
                            # Conflict occurred
                            return False
                        # Record the change
                        action_stack.append((neighbor, neighbor.possible_tiles.copy(), neighbor.collapsed, neighbor.tile, neighbor.entropy))
                        neighbor.possible_tiles = new_possible_tiles
                        neighbor.entropy = neighbor.calculate_entropy(self.tileset)
                        # Add neighbor to the queue if not already in it
                        if neighbor not in queue:
                            queue.append(neighbor)
        return True


    def undo_actions(self, action_stack):
        # Undo the actions in reverse order
        for cell, possible_tiles, collapsed, tile, entropy in reversed(action_stack):
            cell.possible_tiles = possible_tiles
            cell.collapsed = collapsed
            cell.tile = tile
            cell.entropy = entropy

    def get_collapsed_grid(self):
        return [[self.grid[y][x].tile for x in range(self.width)] for y in range(self.height)]
