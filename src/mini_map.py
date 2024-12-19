import pygame

class MiniMap:
    """
    Represents a minimap that displays the dungeon layout, current room, and goal room.

    The MiniMap class handles drawing a scaled-down version of the dungeon map onto the game surface,
    highlighting the player's current position and the goal room.

    Attributes:
        noise_map (List[List[int]]): A 2D list representing the dungeon map layout.
        map_width (int): The width of the map in tiles.
        map_height (int): The height of the map in tiles.
        tile_size (int): The size of each tile in the minimap in pixels.
        minimap_size (Tuple[int, int]): The (width, height) size of the minimap surface in pixels.
        goal_room_coords (Tuple[int, int]): The (x, y) coordinates of the goal room.
    """

    def __init__(self, noise_map, map_width, map_height, goal_room_coords=None, tile_size=4):
        """
        Initializes the MiniMap object.

        Args:
            noise_map (List[List[int]]): A 2D list representing the dungeon map layout.
            map_width (int): The width of the map in tiles.
            map_height (int): The height of the map in tiles.
            goal_room_coords (Tuple[int, int], optional): Coordinates of the goal room to highlight. Defaults to None.
            tile_size (int, optional): Size of each tile in the minimap in pixels. Defaults to 4.
        """
        self.noise_map = noise_map
        self.map_width = map_width
        self.map_height = map_height
        self.tile_size = tile_size
        self.minimap_size = (map_width * tile_size, map_height * tile_size)
        self.goal_room_coords = goal_room_coords

    def draw(self, surface, current_room_coords):
        """
        Draws the minimap onto the given surface.

        The minimap displays all rooms in the dungeon, highlights the goal room in green,
        and the player's current room in red, centered on the game screen.

        Args:
            surface (pygame.Surface): The main game surface to draw the minimap on.
            current_room_coords (Tuple[int, int]): The (x, y) coordinates of the current room.
        """
        # Create a transparent surface for the minimap
        minimap_surface = pygame.Surface(self.minimap_size, pygame.SRCALPHA)
        minimap_surface.fill((0, 0, 0, 0))  # Transparent background

        # Draw each room in the minimap
        for y in range(self.map_height):
            for x in range(self.map_width):
                if self.noise_map[y][x] == 1:
                    color = (255, 255, 255)  # White color for rooms
                    pygame.draw.rect(
                        minimap_surface,
                        color,
                        (x * self.tile_size, y * self.tile_size, self.tile_size, self.tile_size),
                    )

        # Highlight the goal room in green
        if self.goal_room_coords:
            goal_x, goal_y = self.goal_room_coords
            pygame.draw.rect(
                minimap_surface,
                (0, 255, 0),  # Green color for the goal room
                (goal_x * self.tile_size, goal_y * self.tile_size, self.tile_size, self.tile_size),
            )

        # Highlight the current room in red
        room_x, room_y = current_room_coords
        pygame.draw.rect(
            minimap_surface,
            (255, 0, 0),  # Red color for the current room
            (room_x * self.tile_size, room_y * self.tile_size, self.tile_size, self.tile_size),
        )

        # Get the size of the main surface
        surface_width, surface_height = surface.get_size()
        minimap_width, minimap_height = self.minimap_size

        # Calculate the position to center the minimap on the screen
        blit_x = (surface_width - minimap_width) // 2
        blit_y = (surface_height - minimap_height) // 2

        # Blit the minimap surface onto the main surface
        surface.blit(minimap_surface, (blit_x, blit_y))
