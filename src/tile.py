import pygame

TILE_SIZE = 16

class Tile:
    def __init__(self, pos_x, pos_y, tile_type, tile_size=TILE_SIZE, image=None, collidable=False):
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.tile_type = tile_type
        self.tile_size = tile_size
        self.image = image
        self.collidable = collidable
        self.rect = pygame.Rect(
            self.pos_x * self.tile_size,
            self.pos_y * self.tile_size,
            self.tile_size,
            self.tile_size
        )

    def draw(self, surface, camera):
        # Adjust tile drawing based on camera position
        screen_x = self.pos_x * self.tile_size - camera.x
        screen_y = self.pos_y * self.tile_size - camera.y
        surface.blit(self.image, (screen_x, screen_y))