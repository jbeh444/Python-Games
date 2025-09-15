import pgzrun
from random import randint
import json
import os

WIDTH = 1050
HEIGHT = 630
x, y = 35, 595
# ----------------------------
# Actor Initialization
# ----------------------------
# UI Elements
play = Actor("play")       # type: ignore  # noqa: F821
play.pos = 525, 350
dirt = Actor("dirt")       # type: ignore  # noqa: F821
dirt.pos = x, y
# ----------------------------
# Game State Variables
# ----------------------------
playing = False
# ----------------------------
# Dirt Tile Setup
# ----------------------------
dirt_tiles = []
dirt_width = 70
for x in range(0, WIDTH, dirt_width):
    tile = Actor("dirt")
    tile.pos = (x + dirt_width // 2, y)
    dirt_tiles.append(tile)

# ----------------------------
# Gameplay Mechanics
# ----------------------------
placed_blocks = []

def draw():
    global playing
    screen.clear()  # type: ignore  # noqa: F821
    if not playing:
        play.draw()
    else:
        screen.fill((0, 0, 0)) # type: ignore  # noqa: F821 (Erase previous screen)
        screen.draw.text("Game is Running...", center=(WIDTH//2, HEIGHT//2), fontsize=50, color="white") # type: ignore  # noqa: F821
         # Draw dirt across the screen
        for tile in dirt_tiles:
         tile.draw()
        

# def update():
def on_mouse_down(pos, button):
    global playing
    if play.collidepoint(pos):
        print("Play button clicked")
        playing = True
        # Here you can add code to start the game or transition to another screen
def on_key_down(key):
    global playing, y, dirt_tiles, dirt_width, x, WIDTH
    if not playing:
        return
    else:
        if key == keys.DOWN:  # type: ignore  # noqa: F821
            print("Down arrow key pressed")
            if y > 70:
                y = y-70
            for x in range(0, WIDTH, dirt_width):
                tile = Actor("dirt")
                tile.pos = (x + dirt_width // 2, y)
                dirt_tiles.append(tile)
            # Here you can add code to handle the down arrow key press
        if key == keys.ESCAPE:  # type: ignore  # noqa: F821  
            print("Escape key pressed, returning to main menu")
            playing = False
            # Here you can add code to return to the main menu  
        if key == keys.UP:  # type: ignore  # noqa: F821
            print("Up arrow key pressed")            
pgzrun.go()