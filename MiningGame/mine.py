import pgzrun
from random import randint
import pygame
import math

WIDTH = 1050
HEIGHT = 630
dirt_width = 70

# ----------------------------
# Block Class
# ----------------------------
class Block:
    def __init__(self, block_type, pos, health):
        self.actor = Actor(block_type)
        self.actor.pos = pos
        self.health = health
        self.type = block_type
        self.hit_delay = 0

# ----------------------------
# UI Elements
# ----------------------------
play = Actor("play")
play.pos = 525, 315
drill = Actor("drill")

# Orbiting items — clockwise orbit and outward-facing rotation
orbit_items = [
    {"actor": Actor("sword"), "angle": 0, "radius": 113, "speed": 5},
    {"actor": Actor("wood"), "angle": 180, "radius": 90, "speed": 5}
]

# ----------------------------
# Game State Variables
# ----------------------------
playing = False
inventory = {
    "dirt": 0, "gold": 0, "gold2": 0, "gold3": 0,
    "diamond": 0, "diamond2": 0, "diamond3": 0,
    "coal": 0, "stone": 0, "bedrock": 0
}
mined_blocks = []
mined_positions = []

block_types = [
    ("dirt", 50, 10), ("stone", 20, 20), ("coal", 10, 20),
    ("gold", 6, 10), ("gold2", 6, 20), ("gold3", 6, 30),
    ("diamond", 4, 10), ("diamond2", 4, 20), ("diamond3", 4, 30),
    ("bedrock", 2, 30)
]

# ----------------------------
# Dirt Tile Setup
# ----------------------------
dirt_tiles = []
initial_offset = 35
initial_row_y = HEIGHT - dirt_width + initial_offset
first_row = []

for x in range(0, WIDTH, dirt_width):
    block_type, _, health = next(bt for bt in block_types if bt[0] == "dirt")
    tile = Block(block_type, (x + dirt_width // 2, initial_row_y), health)
    first_row.append(tile)
dirt_tiles.append(first_row)

# ----------------------------
# Drawing
# ----------------------------
def draw():
    screen.clear()
    if not playing:
        play.draw()
    else:
        screen.fill((0, 0, 0))
        for row in dirt_tiles:
            for block in row:
                block.actor.draw()
        for block in mined_blocks:
            block.draw()
        drill.draw()
        for item in orbit_items:
            item["actor"].draw()

        row_length = (len(inventory) + 1) // 2
        x_start, y_start = 10, 10
        x_spacing, y_spacing = 150, 40

        for i, (block_type, count) in enumerate(inventory.items()):
            row = i // row_length
            col = i % row_length
            x = x_start + col * x_spacing
            y = y_start + row * y_spacing
            screen.draw.text(f"{block_type.capitalize()}: {count}", topleft=(x, y), fontsize=30, color="white")

# ----------------------------
# Update
# ----------------------------
def update():
    mouse_x, mouse_y = pygame.mouse.get_pos()

    # Drill always follows mouse with fixed offset
    drill.pos = (mouse_x, mouse_y - 175)

    # Orbit around mouse position — clockwise
    for item in orbit_items:
        item["angle"] += item["speed"]
        angle_rad = math.radians(item["angle"])
        dx = math.cos(angle_rad) * item["radius"]
        dy = math.sin(angle_rad) * item["radius"]
        item["actor"].pos = (mouse_x + dx, mouse_y + dy - 45)

        # Restore smooth 360° rotation
        item["actor"].angle = -item["angle"] + 270

    # Drill mining
    for row in dirt_tiles:
        for block in row[:]:
            if block.hit_delay > 0:
                block.hit_delay -= 1
            elif drill.colliderect(block.actor):
                block.health -= 1
                block.hit_delay = 5
                if block.health <= 0:
                    mined = Actor(block.type)
                    mined.pos = block.actor.pos
                    mined_blocks.append(mined)
                    inventory[block.type] += 1
                    mined_positions.append(block.actor.pos)
                    row.remove(block)

    # Orbit item mining
    for item in orbit_items:
        orbit_actor = item["actor"]
        for row in dirt_tiles:
            for block in row[:]:
                if orbit_actor.colliderect(block.actor):
                    if block.hit_delay == 0:
                        block.health -= 1
                        block.hit_delay = 5
                        if block.health <= 0:
                            mined = Actor(block.type)
                            mined.pos = block.actor.pos
                            mined_blocks.append(mined)
                            inventory[block.type] += 1
                            mined_positions.append(block.actor.pos)
                            row.remove(block)

    # Animate mined blocks
    for block in mined_blocks[:]:
        block.y -= 3
        if block.y < -50:
            mined_blocks.remove(block)

    # Auto-generate new row
    if all_blocks_mined():
        max_rows = (HEIGHT - 35) // dirt_width

        for row in dirt_tiles:
            for block in row:
                block.actor.y -= dirt_width
        for i in range(len(mined_positions)):
            x, y = mined_positions[i]
            mined_positions[i] = (x, y - dirt_width)
        if len(dirt_tiles) >= max_rows:
            dirt_tiles.pop(0)

        row_y = HEIGHT - dirt_width + 35
        new_row = []
        for x in range(0, WIDTH, dirt_width):
            block_type = choose_block()
            _, _, health = next(bt for bt in block_types if bt[0] == block_type)
            tile = Block(block_type, (x + dirt_width // 2, row_y), health)
            new_row.append(tile)
        dirt_tiles.append(new_row)

# ----------------------------
# Input Handling
# ----------------------------
def on_mouse_down(pos, button):
    global playing
    if not playing and play.collidepoint(pos):
        playing = True

def on_key_down(key):
    global playing, dirt_tiles, mined_blocks
    if not playing:
        return
    elif key == keys.DOWN:
        print("DOWN key pressed — adding new row")
        max_rows = (HEIGHT - 35) // dirt_width

        for row in dirt_tiles:
            for block in row:
                block.actor.y -= dirt_width
        for i in range(len(mined_positions)):
            x, y = mined_positions[i]
            mined_positions[i] = (x, y - dirt_width)
        if len(dirt_tiles) >= max_rows:
            dirt_tiles.pop(0)

        row_y = HEIGHT - dirt_width + 35
        new_row = []
        for x in range(0, WIDTH, dirt_width):
            block_type = choose_block()
            _, _, health = next(bt for bt in block_types if bt[0] == block_type)
            tile = Block(block_type, (x + dirt_width // 2, row_y), health)
            new_row.append(tile)
        dirt_tiles.append(new_row)

    elif key == keys.UP:
        print("UP key pressed — removing bottom row")
        if dirt_tiles:
            dirt_tiles.pop()
            for row in dirt_tiles:
                for block in row:
                    block.actor.y += dirt_width
            for i in range(len(mined_positions)):
                x, y = mined_positions[i]
                mined_positions[i] = (x, y + dirt_width)

    elif key == keys.ESCAPE:
        print("ESCAPE key pressed — returning to menu")
        playing = False

# ----------------------------
# Helpers
# ----------------------------
def choose_block():
    total = sum(weight for _, weight, _ in block_types)
    pick = randint(1, total)
    current = 0
    for block, weight, _ in block_types:
        current += weight
        if pick <= current:
            return block

def all_blocks_mined():
    return all(len(row) == 0 for row in dirt_tiles)

pgzrun.go()
