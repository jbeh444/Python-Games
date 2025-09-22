import pgzrun
from random import randint
import pygame
import math

WIDTH = 1050
HEIGHT = 630
dirt_width = 70
money = 0

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
    {"actor": Actor("sword"), "angle": 0, "radius": 113, "speed": 5, "damage": 1},
    {"actor": Actor("wood"), "angle": 180, "radius": 90, "speed": 5, "damage": 1},
    {"actor": Actor("pickaxe"), "angle": 90, "radius": 70, "speed": 5, "damage": 1}
]

# Initialization (if not already present)
for item in orbit_items:
    if "max_paid_speed" not in item:
        item["max_paid_speed"] = item["speed"]

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

sell_prices = {
    "dirt": 1, "stone": 2, "coal": 3,
    "gold": 5, "gold2": 10, "gold3": 15,
    "diamond": 8, "diamond2": 16, "diamond3": 24,
    "bedrock": 50
}


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

        # Draw blocks and drill
        for row in dirt_tiles:
            for block in row:
                block.actor.draw()
        for block in mined_blocks:
            block.draw()
        drill.draw()

        # Draw orbiting items
        for item in orbit_items:
            item["actor"].draw()

        # Inventory display (left side)
        row_length = (len(inventory) + 1) // 2
        x_start, y_start = 10, 10
        x_spacing, y_spacing = 150, 30

        for i, (block_type, count) in enumerate(inventory.items()):
            row = i // row_length
            col = i % row_length
            x = x_start + col * x_spacing
            y = y_start + row * y_spacing

            # Alternate colors for readability
            color = "white" if i % 2 == 0 else "lightblue"
            screen.draw.text(f"{block_type.capitalize()}: {count}", topleft=(x, y), fontsize=30, color=color)

        # Top-right HUD
        hud_x = WIDTH - 250
        screen.draw.text(f"Drill Speed: {orbit_items[0]['speed']}", topleft=(hud_x, 10), fontsize=30, color="yellow")
        screen.draw.text(f"Money: ${money}", topleft=(hud_x, 40), fontsize=30, color="lime")

        # Upgrade info (below inventory, shifted up 50px)
        upgrade_y_start = y_start + (row_length * y_spacing) - 60
        sword_cost = orbit_items[0]["damage"] * 15
        wood_cost = orbit_items[1]["damage"] * 15
        pickaxe_cost = orbit_items[2]["damage"] * 15
        Drill_Speed_Cost = (orbit_items[0]["speed"] + 1) * 5  # Next speed cost
         # Shifted up by 20 pixels
         # Shifted up by 20 pixels

        screen.draw.text(f"Sword DMG: {orbit_items[0]['damage']} (Upgrade: ${sword_cost})",
                         topleft=(x_start, upgrade_y_start), fontsize=30, color="red")
        screen.draw.text(f"Wood DMG: {orbit_items[1]['damage']} (Upgrade: ${wood_cost})",
                         topleft=(x_start, upgrade_y_start + 20), fontsize=30, color="orange")
        screen.draw.text(f"Pickaxe DMG: {orbit_items[2]['damage']} (Upgrade: ${pickaxe_cost})",
                         topleft=(x_start , upgrade_y_start-20), fontsize=30, color="blue")
        screen.draw.text(f"Next Drill Speed Upgrade: ${Drill_Speed_Cost}",
                         topleft=(x_start, upgrade_y_start+40), fontsize=30, color="yellow")

        # Instructions
        screen.draw.text("Press 'D' to upgrade Sword, 'F' to upgrade Wood, Press 'G' to upgrade Pickaxe",
                         topleft=(x_start, upgrade_y_start + 60), fontsize=28, color="gray")
        screen.draw.text("Press 'S' to sell inventory",
                         topleft=(x_start, upgrade_y_start + 80), fontsize=28, color="green")
        screen.draw.text("Press +/- to adjust drill speed",
                    topleft=(x_start, upgrade_y_start + 100), fontsize=28, color="lightgray")
        screen.draw.text("Press UP/DOWN to add/remove rows",
                         topleft=(x_start, upgrade_y_start + 120), fontsize=24, color="lightgray")
        screen.draw.text("Press ESC to return to menu",
                         topleft=(x_start, upgrade_y_start + 140), fontsize=24, color="lightgray")

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
                        block.health -= item["damage"]
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
    global playing, dirt_tiles, mined_blocks, money
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

    elif key == keys.KP_PLUS or key == keys.KP_EQUALS:
        print("PLUS key pressed — attempting to increase orbit speed")

        total_cost = 0
        upgrade_costs = []

        for item in orbit_items:
            next_speed = item["speed"] + 1
            # Only charge if next speed exceeds both 5 and max_paid_speed
            if next_speed > 5 and next_speed > item["max_paid_speed"]:
                cost = next_speed * 5
            else:
                cost = 0
            upgrade_costs.append(cost)
            total_cost += cost

        if money >= total_cost:
            money -= total_cost
            for i, item in enumerate(orbit_items):
                prev_speed = item["speed"]
                item["speed"] += 1
                # Update max_paid_speed if we paid for this upgrade
                if upgrade_costs[i] > 0:
                    item["max_paid_speed"] = item["speed"]
                print(f"{prev_speed} → {item['speed']} speed upgraded")
            print(f"Total cost: ${total_cost}, Money left: ${money}")
        else:
            print(f"Not enough money. Total cost to upgrade all orbit items: ${total_cost}, Money: ${money}")

    elif key == keys.KP_MINUS:
        print("MINUS key pressed — decreasing orbit speed")
        for item in orbit_items:
            item["speed"] = max(1, item["speed"] - 1)
    
    elif key == keys.S:
        print("S key pressed — selling inventory")
       
        for block_type, count in inventory.items():
            price = sell_prices.get(block_type, 0)
            money += price * count
            inventory[block_type] = 0
        print(f"Total money: ${money}")
    
    elif key == keys.D:
        current_dmg = orbit_items[0]["damage"]
        cost = current_dmg * 15  # e.g., $15 per damage level
        if money >= cost:
            money -= cost
            orbit_items[0]["damage"] += 1
            print(f"Sword upgraded! Damage: {orbit_items[0]['damage']}, Cost: ${cost}, Money left: ${money}")
        else:
            print(f"Not enough money. Sword upgrade costs ${cost}, but you have ${money}.")

    elif key == keys.F:
        current_dmg = orbit_items[1]["damage"]
        cost = current_dmg * 15  # e.g., $15 per damage level
        if money >= cost:
            money -= cost
            orbit_items[1]["damage"] += 1
            print(f"Wood upgraded! Damage: {orbit_items[1]['damage']}, Cost: ${cost}, Money left: ${money}")
        else:
            print(f"Not enough money. Wood upgrade costs ${cost}, but you have ${money}.")

    elif key == keys.G:
        current_dmg = orbit_items[1]["damage"]
        cost = current_dmg * 15  # e.g., $15 per damage level
        if money >= cost:
            money -= cost
            orbit_items[2]["damage"] += 1
            print(f"Pickaxe upgraded! Damage: {orbit_items[1]['damage']}, Cost: ${cost}, Money left: ${money}")
        else:
            print(f"Not enough money. Pickaxe upgrade costs ${cost}, but you have ${money}.")
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
