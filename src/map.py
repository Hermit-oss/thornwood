import random
from src.noise import Noise
from src.room import Room

class Map:
    """
    Represents the game map consisting of multiple rooms generated based on Perlin noise.

    The Map class handles the creation and management of rooms, tracks the player's
    current location, and facilitates movement between rooms while ensuring consistent
    room generation using a base seed for randomness.
    """

    def __init__(self, map_width, map_height, base_seed=0):
        """
        Initializes the Map object.

        Args:
            map_width (int): The width of the map in rooms.
            map_height (int): The height of the map in rooms.
            base_seed (int): The base seed for random number generation.
        """
        self.base_seed = base_seed
        self.noise = Noise(map_width, map_height, self.base_seed)
        self.rooms_coordinates = self.get_rooms_coordinates()
        self.rooms_coordinates.sort()  # Ensure consistent order for determinism
        self.rooms = {}

        # Use a local random generator for consistent room selection
        self.random_gen = random.Random(self.base_seed)

        # Consistently select spawn and goal rooms
        self.current_room_coords = self.random_gen.choice(self.rooms_coordinates)
        self.spawn_room_coords = self.current_room_coords

        available_rooms = [
            coord for coord in self.rooms_coordinates if coord != self.current_room_coords
        ]
        if available_rooms:
            self.goal_room_coords = self.random_gen.choice(available_rooms)
        else:
            self.goal_room_coords = self.current_room_coords  # Fallback if only one room exists

    def get_rooms_coordinates(self):
        """
        Generates a list of room coordinates where rooms should be placed based on the noise map.

        Returns:
            List[Tuple[int, int]]: A list of (x, y) coordinates where rooms exist.
        """
        rooms = []
        noise_map = self.noise.get_noise_map()
        for y, row in enumerate(noise_map):
            for x, value in enumerate(row):
                if value == 1:
                    rooms.append((x, y))
        return rooms

    def get_current_room(self):
        """
        Retrieves the current room instance based on the player's current coordinates.

        Returns:
            Room: The current room instance.
        """
        room_coord = self.current_room_coords
        if room_coord not in self.rooms:
            # Generate the room if it doesn't already exist
            is_goal_room = (room_coord == self.goal_room_coords)
            is_spawn_room = (room_coord == self.spawn_room_coords)
            self.rooms[room_coord] = Room(
                room_coord,
                base_seed=self.base_seed,
                is_goal_room=is_goal_room,
                is_spawn_room=is_spawn_room
            )
        return self.rooms[room_coord]

    def move_to_room(self, dx, dy):
        """
        Attempts to move the player to a room in the specified direction.

        Args:
            dx (int): The change in x-coordinate (-1 for left, 1 for right).
            dy (int): The change in y-coordinate (-1 for up, 1 for down).

        Returns:
            Room or None: The new room if movement is possible; otherwise, None.
        """
        current_x, current_y = self.current_room_coords
        new_coords = (current_x + dx, current_y + dy)
        if new_coords in self.rooms_coordinates:
            self.current_room_coords = new_coords
            return self.get_current_room()
        else:
            return None  # Movement not possible; no room in that direction

    def get_current_room_coordinates(self):
        """
        Retrieves the coordinates of the current room.

        Returns:
            Tuple[int, int]: The (x, y) coordinates of the current room.
        """
        return self.current_room_coords

    def get_room_at(self, x, y):
        """
        Retrieves the room at the specified coordinates.

        Args:
            x (int): The x-coordinate of the room.
            y (int): The y-coordinate of the room.

        Returns:
            Room or None: The room instance if it exists; otherwise, None.
        """
        coords = (x, y)
        if coords in self.rooms_coordinates:
            if coords not in self.rooms:
                # Generate the room if it doesn't already exist
                is_goal_room = (coords == self.goal_room_coords)
                is_spawn_room = (coords == self.spawn_room_coords)
                self.rooms[coords] = Room(
                    coords,
                    base_seed=self.base_seed,
                    is_goal_room=is_goal_room,
                    is_spawn_room=is_spawn_room
                )
            return self.rooms[coords]
        else:
            return None  # No room exists at the specified coordinates
