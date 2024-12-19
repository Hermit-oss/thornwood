import pygame

class Camera:
    """
    The Camera class manages the viewport into the game world. It follows a target entity (e.g., the player)
    and ensures that the visible area of the game world is appropriately adjusted based on the target's position,
    while keeping the camera within the bounds of the world.

    Attributes:
        width (int): The width of the camera viewport.
        height (int): The height of the camera viewport.
        world_width (int): The total width of the game world.
        world_height (int): The total height of the game world.
        x (int): The x-coordinate of the camera's top-left corner in the game world.
        y (int): The y-coordinate of the camera's top-left corner in the game world.
    """

    def __init__(self, width, height, world_width, world_height):
        """
        Initializes the Camera object.

        Args:
            width (int): The width of the camera viewport.
            height (int): The height of the camera viewport.
            world_width (int): The total width of the game world.
            world_height (int): The total height of the game world.
        """
        self.width = width
        self.height = height
        self.world_width = world_width
        self.world_height = world_height
        self.x = 0
        self.y = 0

    def update(self, target):
        """
        Updates the camera's position based on the target's position.

        The camera centers on the target entity but stays within the bounds of the game world.

        Args:
            target (pygame.sprite.Sprite): The target entity to follow (e.g., the player).
        """
        # Center the camera on the target
        self.x = target.rect.centerx - self.width // 2
        self.y = target.rect.centery - self.height // 2

        # Clamp the camera position to the bounds of the world
        self.x = max(0, min(self.x, self.world_width - self.width))
        self.y = max(0, min(self.y, self.world_height - self.height))
