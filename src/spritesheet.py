import pygame

TILE_SIZE = 16

class Spritesheet:
    def __init__(self, filename):
        self.sheet = pygame.image.load(filename).convert_alpha()  # Convert with alpha channel support

    def get_image(self, x, y, width, height):
        image = pygame.Surface((width, height), pygame.SRCALPHA)  # Use SRCALPHA for transparency
        image.blit(self.sheet, (0, 0), (x * TILE_SIZE, y * TILE_SIZE, width, height))
        return image