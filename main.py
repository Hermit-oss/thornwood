# main.py
import random
import pygame
import math
import sys
import os
import copy
import json
import hashlib
from src.util import TileJsonLoader
from src.character import Character
from src.spritesheet import Spritesheet
from src.camera import Camera
from src.mini_map import MiniMap
from src.map import Map

BASE_RESOLUTION = (800, 600)
MAP_DIMENSIONS = (100, 100)  # Dimensions of the entire map in rooms
TILE_SIZE = 16
BASE_RANDOM_SEED = 91231  # Define the base random seed

def main():
    pygame.init()
    
    screen = pygame.display.set_mode(BASE_RESOLUTION, pygame.RESIZABLE)
    pygame.display.set_caption("Thornwood")

    clock = pygame.time.Clock()
    
    # Initialize the Map with the base seed
    game_map = Map(MAP_DIMENSIONS[0], MAP_DIMENSIONS[1], base_seed=BASE_RANDOM_SEED)
    current_room = game_map.get_current_room()

    # Initialize the character and camera
    world_width = current_room.tile_map.width * TILE_SIZE
    world_height = current_room.tile_map.height * TILE_SIZE

    # Function to find a non-collidable spawn position
    def find_spawn_position(tile_map):
        # Start from the center of the map
        center_x = tile_map.width // 2
        center_y = tile_map.height // 2
        max_radius = max(tile_map.width, tile_map.height) // 2

        for radius in range(max_radius):
            for y in range(center_y - radius, center_y + radius + 1):
                for x in range(center_x - radius, center_x + radius + 1):
                    if 0 <= x < tile_map.width and 0 <= y < tile_map.height:
                        tile = tile_map.tile_map[y][x]
                        if not tile.collidable:
                            # Calculate position considering the collision rectangle offset
                            position_x = x * TILE_SIZE
                            position_y = y * TILE_SIZE
                            return (position_x, position_y)
        # If no non-collidable tile is found, default to center
        return (center_x * TILE_SIZE, center_y * TILE_SIZE)

    spawn_position = find_spawn_position(current_room.tile_map)
    character = Character(current_room.tile_map.spritesheet, spawn_position, world_width, world_height)
    camera = Camera(BASE_RESOLUTION[0], BASE_RESOLUTION[1], world_width, world_height)
    
    fullscreen = False
    show_minimap = False
    show_debug = True  # Toggle to show debug info

    # Initialize the minimap with the goal room coordinates
    mini_map = MiniMap(game_map.noise.get_noise_map(), MAP_DIMENSIONS[0], MAP_DIMENSIONS[1], goal_room_coords=game_map.goal_room_coords)

    # Update the update_room function to handle enemies
    def update_room(new_room, entry_direction):
        nonlocal current_room, world_width, world_height
        current_room = new_room
        world_width = current_room.tile_map.width * TILE_SIZE
        world_height = current_room.tile_map.height * TILE_SIZE
        character.world_width = world_width
        character.world_height = world_height
        if entry_direction is not None:
            # Adjust character position based on entry direction
            new_position = get_entry_position(current_room.tile_map, entry_direction)
        else:
            # Find a valid spawn position in the room
            new_position = find_spawn_position(current_room.tile_map)
        character.position = pygame.Vector2(new_position)
        character.rect.topleft = new_position
        character.collision_rect.topleft = (
            character.position.x + character.collision_rect_offset[0],
            character.position.y + character.collision_rect_offset[1]
        )
        camera.world_width = world_width
        camera.world_height = world_height

    # Function to get the entry position based on entry direction
    def get_entry_position(tile_map, entry_direction):
        # Determine the initial position based on entry direction
        if entry_direction == 'left':
            x = tile_map.width * TILE_SIZE - TILE_SIZE  # Enter from the right edge
            y = character.position.y  # Keep the same y position
        elif entry_direction == 'right':
            x = 0  # Enter from the left edge
            y = character.position.y
        elif entry_direction == 'up':
            x = character.position.x
            y = tile_map.height * TILE_SIZE - TILE_SIZE  # Enter from the bottom edge
        elif entry_direction == 'down':
            x = character.position.x
            y = 0  # Enter from the top edge
        else:
            x, y = character.position.x, character.position.y  # Default to current position

        # Ensure the position is within the room boundaries
        x = max(0, min(x, tile_map.width * TILE_SIZE - TILE_SIZE))
        y = max(0, min(y, tile_map.height * TILE_SIZE - TILE_SIZE))

        # Find the nearest non-collidable position
        position = find_nearest_non_collidable(tile_map, x, y)
        return position

    # Function to find the nearest non-collidable position
    def find_nearest_non_collidable(tile_map, x, y):
        tile_x = int(x // TILE_SIZE)
        tile_y = int(y // TILE_SIZE)

        max_radius = max(tile_map.width, tile_map.height)
        for radius in range(max_radius):
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    check_x = tile_x + dx
                    check_y = tile_y + dy
                    if 0 <= check_x < tile_map.width and 0 <= check_y < tile_map.height:
                        tile = tile_map.tile_map[check_y][check_x]
                        if not tile.collidable:
                            # Check for objects at this position
                            object_here = False
                            for obj in current_room.objects:
                                if obj.pos_x == check_x and obj.pos_y == check_y:
                                    object_here = True
                                    break
                            if not object_here:
                                # Return the position in pixels
                                return (check_x * TILE_SIZE, check_y * TILE_SIZE)
        # If no suitable position found, return original position
        return (x, y)

    win_condition_met = False
    win_timer = 0  # Timer to track when to close the game after winning
    game_over = False  # Initialize game_over variable

    running = True
    while running:
        dt = clock.tick(60) / 1000.0  # Amount of seconds between each loop

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # Only process input if the game is not over
            if not game_over and not win_condition_met:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_m:
                        show_minimap = not show_minimap
                    if event.key == pygame.K_f:
                        if fullscreen:
                            screen = pygame.display.set_mode(BASE_RESOLUTION, pygame.RESIZABLE)
                            fullscreen = False
                        else:
                            screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                            fullscreen = True
                    if event.key == pygame.K_x:
                        # Check for interaction with objects using the interaction rectangle
                        interacted = False
                        for obj in current_room.objects[:]:  # Iterate over a copy since we may modify the list
                            if character.interaction_rect.colliderect(obj.rect):
                                if obj.object_type in ['rock1', 'rock2']:
                                    # Destroy the rock
                                    current_room.objects.remove(obj)
                                    # Also remove from collidable tiles
                                    if obj in current_room.tile_map.collidable_tiles:
                                        current_room.tile_map.collidable_tiles.remove(obj)
                                    interacted = True
                                    break  # Only destroy one object per key press
                                elif obj.object_type == 'flower':
                                    # Player interacts with the flower
                                    win_condition_met = True
                                    win_timer = 0  # Reset the win timer
                                    interacted = True
                                    break
                        for enemy in current_room.enemies[:]:
                            if character.enemy_interaction_rect.colliderect(enemy.collision_rect):
                                # Kill the enemy
                                current_room.enemies.remove(enemy)
                                # Restore some life to the player
                                character.restore_health(1)  # Adjust the amount as needed
                                break
                        if not interacted:
                            # No interaction occurred
                            pass

        # Only process movement if the game is not over
        if not game_over and not win_condition_met:
            keys = pygame.key.get_pressed()
            dx, dy = 0, 0
            if keys[pygame.K_LEFT]:
                dx -= 1
            if keys[pygame.K_RIGHT]:
                dx += 1
            if keys[pygame.K_UP]:
                dy -= 1
            if keys[pygame.K_DOWN]:
                dy += 1

            # Normalize diagonal movement
            if dx != 0 and dy != 0:
                dx *= math.sqrt(0.5)
                dy *= math.sqrt(0.5)

            character.move(dx, dy, dt, current_room.tile_map)
            camera.update(character)
        else:
            # If game is over, no movement
            dx, dy = 0, 0

        # Update enemies even if the game is over (optional)
        for enemy in current_room.enemies:
            enemy.update(dt, character, current_room.tile_map)

            # Check for collision with the character only if the game is not over
            if not game_over and not win_condition_met:
                if character.collision_rect.colliderect(enemy.collision_rect):
                    # Player takes damage
                    character.take_damage(1)  # Adjust the damage amount as needed

        # Check for game over
        if character.health <= 0:
            win_condition_met = False  # Ensure win condition is not met
            game_over = True
            win_timer += dt
            if win_timer >= 5:
                running = False

        # Handle room transition only if the game is not over
        if not game_over and not win_condition_met:
            if character.room_transition_direction:
                # Attempt to move to the adjacent room
                direction = character.room_transition_direction
                dx, dy = 0, 0
                if direction == 'left':
                    dx = -1
                elif direction == 'right':
                    dx = 1
                elif direction == 'up':
                    dy = -1
                elif direction == 'down':
                    dy = 1
                new_room = game_map.move_to_room(dx, dy)
                if new_room:
                    update_room(new_room, entry_direction=direction)
                    # Reset room transition direction
                    character.room_transition_direction = None
                else:
                    # If there is no room in that direction, reset the character's position to within the room boundaries
                    if direction == 'left':
                        character.position.x = 0
                    elif direction == 'right':
                        character.position.x = world_width - TILE_SIZE
                    elif direction == 'up':
                        character.position.y = 0
                    elif direction == 'down':
                        character.position.y = world_height - TILE_SIZE
                    character.collision_rect.topleft = (
                        character.position.x + character.collision_rect_offset[0],
                        character.position.y + character.collision_rect_offset[1]
                    )
                    character.rect.topleft = character.position
                    # Reset room transition direction
                    character.room_transition_direction = None

            character.move(dx, dy, dt, current_room.tile_map)
            # Update character
            character.update(dt)
            camera.update(character)
        else:
            # Still update character for animations if needed
            character.update(dt)
            camera.update(character)

        if win_condition_met:
            win_timer += dt
            if win_timer >= 5:  # 5 seconds have passed
                running = False  # Exit the game loop

        # Draw everything to an off-screen surface first
        offscreen_surface = pygame.Surface(BASE_RESOLUTION)
        offscreen_surface.fill((0, 0, 0))
        current_room.tile_map.draw(offscreen_surface, camera)
        current_room.draw_objects(offscreen_surface, camera)  # Draw objects before the character
        character.draw(offscreen_surface, camera)

        # Draw the minimap if toggled on
        if show_minimap:
            current_room_coords = game_map.get_current_room_coordinates()
            mini_map.draw(offscreen_surface, current_room_coords)

        # Draw debug info
        if show_debug:
            font = pygame.font.SysFont(None, 24)
            room_coords = game_map.get_current_room_coordinates()
            debug_text = f"Room Coordinates: {room_coords}"
            text_surface = font.render(debug_text, True, (255, 255, 255))
            offscreen_surface.blit(text_surface, (10, 10))

        # Draw enemies
        current_room.draw_enemies(offscreen_surface, camera)

        # If win condition is met, display "YOU WIN!" message
        if win_condition_met:
            font = pygame.font.SysFont(None, 72)
            win_text = "YOU WIN!"
            text_surface = font.render(win_text, True, (255, 255, 0))
            text_rect = text_surface.get_rect(center=(BASE_RESOLUTION[0] // 2, BASE_RESOLUTION[1] // 2))
            offscreen_surface.blit(text_surface, text_rect)

        # If game over, display "GAME OVER" message
        if character.health <= 0:
            font = pygame.font.SysFont(None, 72)
            game_over_text = "GAME OVER"
            text_surface = font.render(game_over_text, True, (255, 0, 0))
            text_rect = text_surface.get_rect(center=(BASE_RESOLUTION[0] // 2, BASE_RESOLUTION[1] // 2))
            offscreen_surface.blit(text_surface, text_rect)

        # Draw health bar
        character.draw_health_bar(offscreen_surface)

        # Get the current screen size
        screen_width, screen_height = screen.get_size()

        # Calculate scale factor while maintaining aspect ratio
        scale_x = screen_width / BASE_RESOLUTION[0]
        scale_y = screen_height / BASE_RESOLUTION[1]
        scale = min(scale_x, scale_y)

        # Calculate the size of the scaled surface
        scaled_width = int(BASE_RESOLUTION[0] * scale)
        scaled_height = int(BASE_RESOLUTION[1] * scale)

        # Scale the off-screen surface
        scaled_surface = pygame.transform.scale(offscreen_surface, (scaled_width, scaled_height))

        # Calculate the position to center the scaled surface on the screen
        x = (screen_width - scaled_width) // 2
        y = (screen_height - scaled_height) // 2

        # Fill the screen with black to handle letterboxing
        screen.fill((0, 0, 0))

        # Blit the scaled surface to the screen
        screen.blit(scaled_surface, (x, y))

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
