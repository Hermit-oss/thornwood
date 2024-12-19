import math

class Cell:
    """
    Represents a single cell in the Wave Function Collapse algorithm grid.

    Each cell maintains a list of possible tiles that can occupy it based on the constraints
    of neighboring cells. Cells can be in a collapsed or uncollapsed state.

    Attributes:
        x (int): The x-coordinate of the cell in the grid.
        y (int): The y-coordinate of the cell in the grid.
        possible_tiles (List[str]): A sorted list of possible tile names that can occupy this cell.
        collapsed (bool): Indicates whether the cell has been collapsed to a single tile.
        tile (Optional[str]): The tile assigned to this cell after collapsing. None if uncollapsed.
        entropy (float): The calculated entropy of the cell based on the weights of possible tiles.
    """

    def __init__(self, x, y, tileset):
        """
        Initializes a Cell instance.

        Args:
            x (int): The x-coordinate of the cell in the grid.
            y (int): The y-coordinate of the cell in the grid.
            tileset (Dict[str, Dict]): A dictionary representing the tileset, where keys are tile names
                and values are dictionaries containing tile properties, including 'weight'.
        """
        self.x = x
        self.y = y
        self.possible_tiles = sorted(tileset.keys())
        self.collapsed = False
        self.tile = None
        self.entropy = self.calculate_entropy(tileset)

    def calculate_entropy(self, tileset):
        """
        Calculates the entropy of the cell based on the weights of its possible tiles.

        The entropy is calculated using the natural logarithm of the sum of the weights of the possible tiles:
        entropy = ln(total_weight)

        Args:
            tileset (Dict[str, Dict]): The tileset dictionary containing tile weights.

        Returns:
            float: The entropy of the cell.
        """
        weights = [tileset[tile]['weight'] for tile in self.possible_tiles]
        total_weight = sum(weights)
        entropy = math.log(total_weight)
        return entropy
