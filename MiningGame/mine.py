import pgzrun
from random import randint
import json
import os
import pygame

WIDTH = 1050
HEIGHT = 630
x, y = 35, 595
# ----------------------------
# Actor Initialization
# ----------------------------
# UI Elements
play = Actor("play")       # type: ignore  # noqa: F821
play.pos = 525, 315
dirt = Actor("dirt")       # type: ignore  # noqa: F821
dirt.pos = x, y
drill = Actor("drill")  # Make sure drill.png is in your images folder

# ----------------------------
# Game State Variables
# ----------------------------
playing = False
inventory = {
    "dirt": 0,
    "gold": 0,
    "gold2": 0,
    "gold3": 0,
    "diamond": 0,
    "diamond2": 0,
    "diamond3": 0,
    "coal": 0,    
    "stone": 0,
    "bedrock": 0
}
mined_blocks = []  # Stores Actor objects that were mined
block_types = [
    ("dirt", 50),
    ("stone", 20),
    ("coal", 10),    
    ("gold", 6),
    ("gold2", 6),
    ("gold3", 6),
    ("diamond", 4),
    ("diamond2", 4),
    ("diamond3", 4),
    ("bedrock", 2)
]
# ----------------------------
# Dirt Tile Setup
# ----------------------------
dirt_tiles = []
dirt_width = 70
mined_positions = []  # Stores (x, y) tuples of mined tiles

# Place the first row using the same logic as DOWN key
initial_offset = 35  # Push tiles 35 pixels lower
initial_row_y = HEIGHT - dirt_width + initial_offset

first_row = []
for x in range(0, WIDTH, dirt_width):
    tile = Actor("dirt")
    tile.pos = (x + dirt_width // 2, initial_row_y)
    first_row.append(tile)
dirt_tiles.append(first_row)
# ----------------------------
# Gameplay Mechanics
# ----------------------------

def draw():
    screen.clear() #type: ignore 
    if not playing:
        play.draw()
    else:
        screen.fill((0, 0, 0)) #type: ignore        
        
        for row in dirt_tiles:
            for tile in row:
                tile.draw()

        for block in mined_blocks:
            block.draw()

        drill.draw()
        row_length = (len(inventory) + 1) // 2  # Split items roughly evenly across 2 rows
        x_start = 10
        y_start = 10
        x_spacing = 150
        y_spacing = 40

        for i, (block_type, count) in enumerate(inventory.items()):
            row = i // row_length
            col = i % row_length
            x = x_start + col * x_spacing
            y = y_start + row * y_spacing
            screen.draw.text(f"{block_type.capitalize()}: {count}", topleft=(x, y), fontsize=30, color="white")

def is_block_below(tile):
    for row in dirt_tiles:
        for other in row:
            # Check if there's a tile directly below
            same_column = abs(other.x - tile.x) < dirt_width
            directly_below = abs(other.y - (tile.y + dirt_width)) < 5
            if same_column and directly_below:
                return True
    return False

def find_lowest_empty_row():
    for i in range(len(dirt_tiles)):
        if len(dirt_tiles[i]) == 0:
            return i
    return len(dirt_tiles)  # If no empty row, place on top

def find_highest_non_empty_row():
    for i in reversed(range(len(dirt_tiles))):
        if len(dirt_tiles[i]) > 0:
            return i
    return None  # No non-empty rows found


def update():
    mouse_x, mouse_y = pygame.mouse.get_pos()
    drill.pos = (mouse_x, mouse_y - 175)
    # Assuming drill is an Actor
    for row_index, row in enumerate(dirt_tiles):
        for col_index, tile in enumerate(row):
            if drill.colliderect(tile):
                # Optional: check if there's a tile below
                # if is_block_below(tile):
                #     print("Cannot mine: block below")
                #     return

                # Mine the tile
                mined = Actor(tile.image)
                mined.pos = tile.pos
                mined_blocks.append(mined)
                row.remove(tile)
                inventory[tile.image] += 1
                mined_positions.append(tile.pos)
                print(f"Mined block at {tile.pos}")

                # Check if all blocks are mined
                if all(len(row) == 0 for row in dirt_tiles):
                    print("All blocks mined — resetting terrain")
                    dirt_tiles.clear()
                    mined_positions.clear()
                return  # Exit after mining one block to avoid multiple removals per frame

    for block in mined_blocks[:]:
        block.y -= 3
        if block.y < -50:
            mined_blocks.remove(block)

   

def on_mouse_down(pos, button):
    global playing
    if not playing:
        if play.collidepoint(pos):
            print("Play button clicked")
            playing = True
    # else:
    #     for row_index, row in enumerate(dirt_tiles):
    #         for col_index, tile in enumerate(row):
    #             if tile.collidepoint(pos):
    #                 # Check if there's a tile below using position-based logic
    #                 # if is_block_below(tile):
    #                 #     print("Cannot mine: block below")
    #                 #     return

    #                 # Mine the tile
    #                 mined = Actor(tile.image)
    #                 mined.pos = tile.pos
    #                 mined_blocks.append(mined)
    #                 row.remove(tile)
    #                 inventory[tile.image] += 1
    #                 mined_positions.append(tile.pos)
    #                 print(f"Mined block at {tile.pos}")

    #                 # Check if all blocks are mined
    #                 if all(len(row) == 0 for row in dirt_tiles):
    #                     print("All blocks mined — resetting terrain")
    #                     dirt_tiles.clear()
    #                     mined_positions.clear()

                        # # Rebuild bottom row
                        # initial_offset = 35
                        # row_y = HEIGHT - dirt_width + initial_offset
                        # new_row = []
                        # for x in range(0, WIDTH, dirt_width):
                        #     block_type = choose_block()
                        #     tile = Actor(block_type)
                        #     tile.pos = (x + dirt_width // 2, row_y)
                        #     new_row.append(tile)
                        # dirt_tiles.append(new_row)

                    # return




               
def on_key_down(key):
    global playing, dirt_tiles, mined_blocks, dirt_width, WIDTH
    if not playing:
        return
    elif key == keys.DOWN:
        print("Down arrow key pressed")
        max_rows = (HEIGHT - 35) // dirt_width

        # Shift all rows UP
        for row in dirt_tiles:
            for tile in row:
                tile.y -= dirt_width

        # Shift mined positions UP
        for i in range(len(mined_positions)):
            x, y = mined_positions[i]
            mined_positions[i] = (x, y - dirt_width)

        # Remove top row if we've exceeded max height
        if len(dirt_tiles) >= max_rows:
            dirt_tiles.pop(0)

        # Add new row at the bottom
        row_y = HEIGHT - dirt_width + 35
        new_row = []
        for x in range(0, WIDTH, dirt_width):
            block_type = choose_block()
            tile = Actor(block_type)
            tile.pos = (x + dirt_width // 2, row_y)
            new_row.append(tile)
        dirt_tiles.append(new_row)

    elif key == keys.UP:
        print("Up arrow key pressed")

        if dirt_tiles:
            # Remove bottom row
            dirt_tiles.pop()

            # Shift remaining tiles DOWN
            for row in dirt_tiles:
                for tile in row:
                    tile.y += dirt_width

            # Shift mined positions DOWN
            for i in range(len(mined_positions)):
                x, y = mined_positions[i]
                mined_positions[i] = (x, y + dirt_width)

    elif key == keys.ESCAPE:
        print("Escape key pressed, returning to main menu")
        playing = False
    
def choose_block():
    total = sum(weight for _, weight in block_types)
    pick = randint(1, total)
    current = 0
    for block, weight in block_types:
        current += weight
        if pick <= current:
            return block

def count_visible_blocks():
    counts = {
        "dirt": 0,
        "stone": 0,
        "coal": 0,
        "gold": 0,
        "diamond": 0,
        "bedrock": 0
    }
    for row in dirt_tiles:
        for tile in row:
            if tile.image in counts:
                counts[tile.image] += 1
    return counts
                       
pgzrun.go()