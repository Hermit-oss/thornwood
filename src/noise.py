import math
import random

NEIGHBOR_WALLS = 4
DENSITY = 60
TILE_SIZE = 16
DEFAULT_ROOM_VALUE = 1
DEFAULT_NONR_VALUE = 0
DEFAULT_FLOOR_VALUE = 1
DEFAULT_WALL_VALUE = 0

class Noise:
    def __init__(self, width, height, seed=None, density=45, neighbor_walls=4, smooth_iterations=6):
        """
        Generates a noise map using cellular automata for dungeon generation.

        Parameters:
        - width (int): Width of the map.
        - height (int): Height of the map.
        - seed (int, optional): Random seed for reproducibility. If None, a random seed is used.
        - density (int): Initial fill percentage (0-100) for the map.
        - neighbor_walls (int): Threshold of wall neighbors to consider a cell as a wall.
        - smooth_iterations (int): Number of smoothing iterations using cellular automata.
        """
        self.width = width
        self.height = height
        self.density = density
        self.neighbor_walls = neighbor_walls
        self.smooth_iterations = smooth_iterations

        if seed is None:
            seed = random.randint(0, 1000)
        self.seed = seed
        random.seed(self.seed)

        self.noise_map = [[0 for _ in range(self.width)] for _ in range(self.height)]  # Initialize with walls
        self.generate_initial_noise()
        self.apply_cellular_automaton()
        self.fully_connect_rooms()

    def generate_initial_noise(self):
        """
        Generates the initial random noise map.
        """
        center_x = self.width / 2
        center_y = self.height / 2
        max_radius = 0.5 * min(self.width, self.height)

        for y in range(self.height):
            for x in range(self.width):
                # Calculate distance from the center to create a circular map
                distance = math.hypot(x - center_x, y - center_y)
                if distance > max_radius:
                    # Outside the circle, keep as wall
                    continue
                else:
                    # Inside the circle, randomly assign as floor or wall based on density
                    self.noise_map[y][x] = 1 if random.randint(1, 100) < self.density else 0

    def apply_cellular_automaton(self):
        """
        Applies cellular automaton rules to smooth the noise map.
        """
        for _ in range(self.smooth_iterations):
            new_map = [[0 for _ in range(self.width)] for _ in range(self.height)]
            for y in range(self.height):
                for x in range(self.width):
                    walls = self.count_adjacent_walls(x, y)
                    if walls > self.neighbor_walls:
                        new_map[y][x] = 0  # Wall
                    else:
                        new_map[y][x] = 1  # Floor
            self.noise_map = new_map

    def count_adjacent_walls(self, x, y):
        """
        Counts the number of wall tiles adjacent to a given cell.

        Returns:
        - walls (int): Number of adjacent wall tiles.
        """
        walls = 0
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                nx, ny = x + dx, y + dy
                if dx == 0 and dy == 0:
                    continue  # Skip the center cell
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if self.noise_map[ny][nx] == 0:
                        walls += 1
                else:
                    # Consider out-of-bounds as wall
                    walls += 1
        return walls

    def flood_fill(self, x, y, room, visited):
        """
        Performs a flood fill algorithm to find all connected floor tiles.

        Parameters:
        - x, y (int): Starting coordinates.
        - room (list): List to store the coordinates of the room's floor tiles.
        - visited (set): Set of visited coordinates to avoid repetition.
        """
        stack = [(x, y)]
        while stack:
            cx, cy = stack.pop()
            if (cx, cy) in visited:
                continue
            visited.add((cx, cy))
            if self.noise_map[cy][cx] == 1:
                room.append((cx, cy))
                # Check all four cardinal directions
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        stack.append((nx, ny))

    def find_rooms(self):
        """
        Identifies all separate rooms (connected floor regions) in the map.

        Returns:
        - rooms (list): List of rooms, each room is a list of (x, y) tuples.
        """
        visited = set()
        rooms = []
        for y in range(self.height):
            for x in range(self.width):
                if self.noise_map[y][x] == 1 and (x, y) not in visited:
                    room = []
                    self.flood_fill(x, y, room, visited)
                    rooms.append(room)
        return rooms

    def euclidean_distance(self, coordinate1, coordinate2):
        """
        Calculates the Euclidean distance between two coordinates.

        Returns:
        - distance (float): The Euclidean distance.
        """
        x1, y1 = coordinate1
        x2, y2 = coordinate2
        return math.hypot(x2 - x1, y2 - y1)

    def find_closest_cells(self, room1, room2):
        """
        Finds the closest pair of tiles between two rooms.

        Returns:
        - (cell1, cell2): The closest pair of coordinates between the two rooms.
        """
        min_distance = float('inf')
        closest_pair = (None, None)
        for cell1 in room1:
            for cell2 in room2:
                distance = self.euclidean_distance(cell1, cell2)
                if distance < min_distance:
                    min_distance = distance
                    closest_pair = (cell1, cell2)
        return closest_pair

    def connect_rooms(self, room1, room2):
        """
        Connects two rooms by creating a corridor between them.

        Parameters:
        - room1, room2 (list): Lists of (x, y) coordinates representing the rooms.
        """
        cell1, cell2 = self.find_closest_cells(room1, room2)
        if cell1 and cell2:
            corridor = self.bresenham_line(cell1[0], cell1[1], cell2[0], cell2[1])
            for x, y in corridor:
                if 0 <= x < self.width and 0 <= y < self.height:
                    self.noise_map[y][x] = 1  # Create floor for the corridor

    def bresenham_line(self, x1, y1, x2, y2, thickness=1):
        """
        Generates a list of coordinates forming a thicker line between two points using Bresenham's algorithm.

        Parameters:
        - x1, y1, x2, y2 (int): Coordinates of the start and end points.
        - thickness (int): Thickness of the corridor to be drawn.

        Returns:
        - points (list): List of (x, y) tuples along the line and around it for the thickness.
        """
        points = []
        dx = abs(x2 - x1)
        dy = -abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx + dy

        while True:
            # Add the main point
            points.append((x1, y1))

            # Add surrounding points for thickness
            for offset_x in range(-thickness, thickness + 1):
                for offset_y in range(-thickness, thickness + 1):
                    nx, ny = x1 + offset_x, y1 + offset_y
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        points.append((nx, ny))  # Add thick line points

            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x1 += sx
            if e2 <= dx:
                err += dx
                y1 += sy

        return points

    def fully_connect_rooms(self):
        """
        Ensures that all rooms are connected by corridors, forming a fully connected dungeon.
        """
        rooms = self.find_rooms()
        if not rooms:
            return
        connected_rooms = [rooms.pop(0)]
        while rooms:
            room1 = connected_rooms[-1]
            min_distance = float('inf')
            closest_room = None
            closest_cells = None
            for room2 in rooms:
                cell1, cell2 = self.find_closest_cells(room1, room2)
                distance = self.euclidean_distance(cell1, cell2)
                if distance < min_distance:
                    min_distance = distance
                    closest_room = room2
                    closest_cells = (cell1, cell2)
            self.connect_rooms(room1, closest_room)
            connected_rooms.append(closest_room)
            rooms.remove(closest_room)

    def get_noise_map(self):
        """
        Retrieves the generated noise map.

        Returns:
        - noise_map (list): The 2D list representing the dungeon map.
        """
        return self.noise_map

    def return_random_floor_cell(self):
        """
        Returns a random floor tile from the map.

        Returns:
        - (x, y) (tuple): Coordinates of a floor tile, or None if no floor tiles exist.
        """
        floor_cells = [(x, y) for y in range(self.height) for x in range(self.width) if self.noise_map[y][x] == 1]
        return random.choice(floor_cells) if floor_cells else None


# import matplotlib.pyplot as plt

# def display_map(noise_map):
#     """
#     Displays the generated noise map using matplotlib.

#     Parameters:
#     - noise_map (list of lists): The 2D map to display, where 0 represents walls and 1 represents floors.
#     """
#     plt.figure(figsize=(10, 10))
#     plt.imshow(noise_map, cmap='gray', origin='upper')
#     plt.title('Generated Dungeon Map')
#     plt.axis('off')  # Hide the axes for better visualization
#     plt.show()

# if __name__ == "__main__":
#     # Define the dimensions of the map
#     width, height = 100, 100  # You can adjust these values as needed

#     # Create an instance of the Noise class with desired parameters
#     noise = Noise(
#         width=width,
#         height=height,
#         seed=None,               # You can set a specific seed for reproducibility
#         density=45,         # Initial fill percentage
#         neighbor_walls=NEIGHBOR_WALLS,  # Threshold for wall neighbors
#         smooth_iterations=6      # Number of smoothing iterations
#     )

#     # Retrieve the generated noise map
#     generated_map = noise.get_noise_map()

#     # Display the map using matplotlib
#     display_map(generated_map)