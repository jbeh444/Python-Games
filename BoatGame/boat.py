import pgzrun
from random import randint
import json
import os

# ----------------------------
# Window Settings
# ----------------------------
WIDTH = 1000
HEIGHT = 600

# ----------------------------
# Shop Item Definitions
# ----------------------------
shop_items = {
    "wood": {"price": 50},
    "stone": {"price": 100},
    "metal": {"price": 500},
    "flag": {"price": 1000},
    "obsidian": {"price": 2000},
    "rug": {"price": 100}
}

# ----------------------------
# Actor Initialization
# ----------------------------
# UI Elements
shop = Actor("shop")       # type: ignore  # noqa: F821
shop.pos = 900, 300

sail = Actor("sail")       # type: ignore  # noqa: F821
sail.pos = 900, 200

play = Actor("play")       # type: ignore  # noqa: F821
play.pos = 500, 257

levels = Actor("levels")     # type: ignore  # noqa: F821
levels.pos = 900, 400

exit = Actor("exit")       # type: ignore  # noqa: F821
exit.pos = 500, 200

# Blocks
woodblock = Actor("woodblock")       # type: ignore  # noqa: F821
woodblock.pos = 90, 250

stoneblock = Actor("stoneblock")     # type: ignore  # noqa: F821
stoneblock.pos = 150, 250

metalblock = Actor("metalblock")     # type: ignore  # noqa: F821
metalblock.pos = 210, 250

flag = Actor("flag")       # type: ignore  # noqa: F821
flag.pos = 270, 250

obsidianblock = Actor("obsidianblock")  # type: ignore  # noqa: F821
obsidianblock.pos = 330, 250

rugblock = Actor("rugblock")  # type: ignore  # noqa: F821
rugblock.pos = 390, 250

# Game Objects
# Level 1
rock = Actor("rock")       # type: ignore  # noqa: F821
rx = 1100
ry = randint(350, 550)
rock.pos = rx, ry

#level 2 
rock2 = Actor("rock2")  # type: ignore  # noqa: F821
r2x = 1500
r2y = randint(390, 550)
rock2.pos = r2x, r2y
meteor = Actor("meteor")  # type: ignore  # noqa: F821
mx = randint(300, 1000)
my = -600
meteor.pos = mx, my

#End of level
treasurechest = Actor("tresurechest")  # type: ignore  # noqa: F821
treasurechest.pos = 1600, 400

# ----------------------------
# Game State Variables
# ----------------------------
sail_clicked_fun = False
music_playing = False
flagplaced = False
playing = False
load_game_once = False
level = 1
# ----------------------------
# Inventory & Gameplay Stats
# ----------------------------
number_of_rocks = 99 #set to zero whenrunning the game for the first time
money = 0
woodcount = 5
placedwood = 0
stoneblockcount = 2
placedstone = 0
metalblockcount = 1
placedmetal = 0
flagcount = 1
placedflagcount = 0
obsidianblockcount = 0
placedobsidian = 0  
rugblockcount = 2
placedrug = 0
missed_rocks = 0

# ----------------------------
# Gameplay Mechanics
# ----------------------------
selected_block = None
placed_blocks = []


def draw():
    global sail_clicked_fun
    screen.blit("ocean", (0, 0)) # type: ignore  # noqa: F821
    if playing:
        if sail_clicked_fun and music_playing: 
            if number_of_rocks >= 100:
                treasurechest.draw()   #draw treasure chest   
            else:
                rock.draw() #draw rock
                exit.draw() #draw exit button
                if level >1:
                    rock2.draw()
                    meteor.draw()
            for block in placed_blocks:
                block["actor"].draw()

            screen.draw.text("Money: " + str(money), (500, 10), color="black") # type: ignore  # noqa: F821
        else:           
            #Drawing lines (Start position->(x.pos, y.pos), Stop position->(x.pos, y.pos), color)
            #Horizontal
            woodblock.draw()
            stoneblock.draw()
            metalblock.draw()
            flag.draw()
            obsidianblock.draw()
            rugblock.draw()           
            
            for block in placed_blocks:
                block["actor"].draw()           
            
            screen.draw.text("Money: " + str(money), (850, 520), color="black") # type: ignore  # noqa: F821
                     
            # Draw horizontal grid lines
            for y in range(286, 600, 60):
                screen.draw.line((0, y), (600, y), color="black") # type: ignore  # noqa: F821

            # Draw vertical grid lines
            for x in range(60, 601, 60):
                screen.draw.line((x, 286), (x, 586), color="black") # type: ignore  # noqa: F821

            # Build menu horizontal lines
            screen.draw.line((60, 220), (420, 220), color="black") # type: ignore  # noqa: F821
            screen.draw.line((60, 280), (420, 280), color="black") # type: ignore  # noqa: F821            
            
            # Build menu vertical dividers
            for x in range(60, 421, 60):
                screen.draw.line((x, 220), (x, 280), color="black") # type: ignore  # noqa: F821
            
            
           # Prices
            screen.draw.text("Press shop to buy selected block", (60, 140), color="black", fontsize=18) # type: ignore  # noqa: F821
            screen.draw.text("$50", (80, 200), color="black", fontsize=18) # type: ignore  # noqa: F821
            screen.draw.text("$100", (136, 200), color="black", fontsize=18) # type: ignore  # noqa: F821
            screen.draw.text("$500", (193, 200), color="black", fontsize=18) # type: ignore  # noqa: F821
            screen.draw.text("$1000", (250, 200), color="black", fontsize=18) # type: ignore  # noqa: F821
            screen.draw.text("$2000", (310, 200), color="black", fontsize=18) # type: ignore  # noqa: F821
            screen.draw.text("$100", (373, 200), color="black", fontsize=18) # type: ignore  # noqa: F821

            # Counts
            screen.draw.text("Wood:", (70, 160), color="black", fontsize=20) # type: ignore  # noqa: F821
            screen.draw.text(str(woodcount), (83, 180), color="black", fontsize=20) # type: ignore  # noqa: F821
            
            screen.draw.text("Stone:", (130, 160), color="black", fontsize=20) # type: ignore  # noqa: F821
            screen.draw.text(str(stoneblockcount), (145, 180), color="black", fontsize=20) # type: ignore  # noqa: F821
            
            screen.draw.text("Metal:", (190, 160), color="black", fontsize=20) # type: ignore  # noqa: F821
            screen.draw.text(str(metalblockcount), (200, 180), color="black", fontsize=20) # type: ignore  # noqa: F821
            
            screen.draw.text("Flag:", (255, 160), color="black", fontsize=20) # type: ignore  # noqa: F821
            screen.draw.text(str(flagcount), (260, 180), color="black", fontsize=20) # type: ignore  # noqa: F821
            
            screen.draw.text("Obsidian:", (300, 160), color="black", fontsize=20) # type: ignore  # noqa: F821
            screen.draw.text(str(obsidianblockcount), (325, 180), color="black", fontsize=20) # type: ignore  # noqa: F821
            
            screen.draw.text("Rug:", (375, 160), color="black", fontsize=20) # type: ignore  # noqa: F821
            screen.draw.text(str(rugblockcount), (385, 180), color="black", fontsize=20) # type: ignore  # noqa: F821
            
            screen.draw.text("Level: ", (820, 445), color="black", fontsize=20) # type: ignore  # noqa: F821
            screen.draw.text(str(level), (860, 445), color="black", fontsize=20) # type: ignore  # noqa: F821

            sail.draw()
            shop.draw()
            levels.draw()
    else:
        play.draw()
    
def on_mouse_down(pos, button):
    global playing, selected_block
    if exit.collidepoint(pos):
        restart_game()
    if not playing or not sail_clicked_fun:  # 🔒 Only allow input before sailing
        if button == mouse.LEFT: # type: ignore  # noqa: F821
            if sail.collidepoint(pos):
                sail_clicked()
            elif shop.collidepoint(pos):
                open_shop_menu()
            elif levels.collidepoint(pos):
                open_levels_menu()  # Assuming you have a function to handle levels
            elif play.collidepoint(pos) and not sail_clicked_fun:
                playing = True
            elif woodblock.collidepoint(pos):
                selected_block = "wood"                
            elif stoneblock.collidepoint(pos):
                selected_block = "stone"
            elif metalblock.collidepoint(pos):
                selected_block = "metal"
            elif flag.collidepoint(pos):
                selected_block = "flag"    
            elif obsidianblock.collidepoint(pos):
                selected_block = "obsidian"
            elif rugblock.collidepoint(pos):
                selected_block = "rug"
            else:
                place_block(pos)
        elif button == mouse.RIGHT: # type: ignore  # noqa: F821
            delete_block(pos)

def open_shop_menu():
    global money, woodcount, stoneblockcount, metalblockcount, flagcount, obsidianblockcount, rugblockcount
    if selected_block and selected_block in shop_items:
        cost = shop_items[selected_block]["price"]
        if money >= cost:
            money -= cost
            if selected_block == "wood":
                woodcount += 1                
            elif selected_block == "stone":
                stoneblockcount += 1
            elif selected_block == "metal":
                metalblockcount += 1
            elif selected_block == "flag":
                flagcount += 1
            elif selected_block == "obsidian":
                obsidianblockcount += 1 
            elif selected_block == "rug":
                rugblockcount += 1
        
        
def sail_clicked():
    global sail_clicked_fun, music_playing

    # Prevent sailing if only a flag or no blocks
    non_flag_blocks = [b for b in placed_blocks if b["type"] != "flag"]
    if not non_flag_blocks:
        return  # Block sailing

    sail_clicked_fun = True
    if not music_playing:
        music.play("vanishing-horizon") # type: ignore  # noqa: F821
        music_playing = True

def open_levels_menu():
    global level
    # Here you can implement the logic to open a levels menu
    # For now, let's just print the current level
    print(f"Current Level: {level}")
    # You can add more functionality here to change levels or display level information       
        
def update():
    global rock, number_of_rocks, treasurechest, sail_clicked_fun, money, music_playing, sail_clicked_fun
    global placed_blocks, flagplaced, flagcount, woodcount, stoneblockcount, metalblockcount, missed_rocks, money, placedrug, placedobsidian
    global load_game_once, placedwood, placedstone, placedmetal, placedflagcount, obsidianblockcount, rugblockcount, level, rock2, meteor 
    if not load_game_once:
        load_game()  # Load game state at the start 
    if sail_clicked_fun:
        
        if rock.left > 0:        
            rock.x -= 5
            
            for block in placed_blocks[:]:
                if rock.colliderect(block["actor"]):
                    block["health"] -= 1
                    if block["health"] <= 0:
                        # Refill the count based on block type
                        if block["type"] == "wood":
                            woodcount += 1
                            placedwood -= 1
                        elif block["type"] == "stone":
                            stoneblockcount += 1
                            placedstone -= 1
                        elif block["type"] == "metal":
                            metalblockcount += 1
                            placedmetal -= 1
                        elif block["type"] == "flag":
                            flagcount += 1
                            placedflagcount -= 1
                        elif block["type"] == "obsidian":
                            obsidianblockcount += 1
                            placedobsidian -= 1
                        elif block["type"] == "rug":
                            rugblockcount += 1
                            placedrug -= 1
                        placed_blocks.remove(block)
                    # Rock hit something, reset
                    rock.x = 1100
                    rock.y = randint(350, 550)
                    number_of_rocks += 1
                    missed_rocks = 0
                    money += 8
                    break
        else:
            # Rock missed everything, still reset!
            rock.x = 1100

            if missed_rocks >= 2:
                # Try upper and lower positions alternately
                if missed_rocks == 2:
                    rock.y = 350  # Upper range
                else:
                    rock.y = 550  # Lower range
            else:
                rock.y = randint(350, 550)  # Default range

            number_of_rocks += 1
            missed_rocks += 1
            money += 8
            
        if level > 1:
            if rock2.left > 0:
                rock2.x -= 5
                for block in placed_blocks[:]:
                    if rock2.colliderect(block["actor"]):
                        block["health"] -= 2
                        if block["health"] <= 0:
                            # Refill the count based on block type
                            if block["type"] == "wood":
                                woodcount += 1
                                placedwood -= 1
                            elif block["type"] == "stone":
                                stoneblockcount += 1
                                placedstone -= 1
                            elif block["type"] == "metal":
                                metalblockcount += 1
                                placedmetal -= 1
                            elif block["type"] == "flag":
                                flagcount += 1
                                placedflagcount -= 1
                            elif block["type"] == "obsidian":
                                obsidianblockcount += 1
                                placedobsidian -= 1
                            elif block["type"] == "rug":
                                rugblockcount += 1
                                placedrug -= 1
                            placed_blocks.remove(block)
                        # Rock hit something, reset
                        rock2.x = 1500
                        rock2.y = randint(390, 550)
                        number_of_rocks += 1
                        missed_rocks = 0
                        money += 16
                        break
            else:
                # Rock missed everything, still reset!
                rock2.x = 1500

                if missed_rocks >= 2:
                    # Try upper and lower positions alternately
                    if missed_rocks == 2:
                        rock2.y = 390  # Upper range
                    else:
                        rock2.y = 550  # Lower range
                else:   
                    rock2.y = randint(390, 550)

            if meteor.bottom < HEIGHT:
                meteor.y += 7
                meteor.x -= 3
                for block in placed_blocks[:]:
                    if meteor.colliderect(block["actor"]):
                        block["health"] -= 2
                        if block["health"] <= 0:
                            # Refill the count based on block type
                            if block["type"] == "wood":
                                woodcount += 1
                                placedwood -= 1
                            elif block["type"] == "stone":
                                stoneblockcount += 1
                                placedstone -= 1
                            elif block["type"] == "metal":
                                metalblockcount += 1
                                placedmetal -= 1
                            elif block["type"] == "flag":
                                flagcount += 1
                                placedflagcount -= 1
                            elif block["type"] == "obsidian":
                                obsidianblockcount += 1
                                placedobsidian -= 1
                            elif block["type"] == "rug":
                                rugblockcount += 1
                                placedrug -= 1
                            placed_blocks.remove(block)
                        # Rock hit something, reset
                        meteor.pos = (randint(300, 1000), -300)
                        number_of_rocks += 1
                        missed_rocks = 0
                        money += 24
                        break
            else:
                meteor.pos = (randint(300, 1000), -300)
                number_of_rocks += 1
                money += 16 
                
         # Check if the flag is broken
        flag_broken = not any(block["type"] == "flag" for block in placed_blocks)

        # Check if no blocks are left
        no_blocks_left = len(placed_blocks) == 0

        if flag_broken or no_blocks_left:
            restart_game()  

        if number_of_rocks >= 100:
            if treasurechest.right > 0:
                treasurechest.x -= 5
                rock.x = 1600 # Reset rock position
                rock2.x = 1600
                meteor.y= -300
                # Check if the treasure chest collides with any placed blocks
                for block in placed_blocks[:]:
                    if treasurechest.colliderect(block["actor"]):
                        money += 1000 * level
                        level += 1
                        treasurechest.pos = (-200, 400)
                        restart_game()
                        break
                
                else:
                    if treasurechest.left < 0:
                        money += 1000 * level
                        level += 1
                        treasurechest.pos = (-200, 400)
                        restart_game()
                        
def place_block(pos):
    global selected_block, woodcount, stoneblockcount, metalblockcount, flagcount, placedwood, placedstone, placedmetal, placedflagcount
    global placed_blocks, obsidianblockcount, rugblockcount
    global health, placedobsidian, placedrug
    if selected_block:
        x, y = pos
        if 0 <= x <= 590 and 303 <= y < 583:
            grid_x = (x // 60) * 60 + 30
            grid_y = (y // 60) * 60 + 17

            # Check if a block is already placed here
            for block in placed_blocks:
                if block["actor"].pos == (grid_x, grid_y):

                    return  # Don't place over another block

            new_block = None
            if selected_block == "wood" and woodcount > 0:
                new_block = Actor("woodblock") # type: ignore  # noqa: F821
                woodcount -= 1
                placedwood += 1
            elif selected_block == "stone" and stoneblockcount > 0:
                new_block = Actor("stoneblock") # type: ignore  # noqa: F821
                stoneblockcount -= 1
                placedstone += 1
            elif selected_block == "metal" and metalblockcount > 0:
                new_block = Actor("metalblock") # type: ignore  # noqa: F821
                metalblockcount -= 1
                placedmetal += 1
            elif selected_block == "flag" and flagcount > 0:
                new_block = Actor("flag") # type: ignore  # noqa: F821
                flagcount -= 1
                placedflagcount += 1
            elif selected_block == "obsidian" and obsidianblockcount > 0:
                new_block = Actor("obsidianblock") # type: ignore  # noqa: F821
                obsidianblockcount -= 1
                placedobsidian += 1
            elif selected_block == "rug" and rugblockcount > 0:
                new_block = Actor("rugblock") # type: ignore  # noqa: F821
                rugblockcount -= 1
                placedrug += 1

            if new_block:
                new_block.pos = (grid_x, grid_y)

                if selected_block == "wood":
                    health = 1
                elif selected_block == "stone":
                    health = 2
                elif selected_block == "metal":
                    health = 9
                elif selected_block == "flag":
                    health = 1
                elif selected_block == "obsidian":
                    health = 14
                elif selected_block == "rug":
                    health = 2

                placed_blocks.append({
                    "actor": new_block,
                    "type": selected_block,  # ← Add this line
                    "health": health
                })

def delete_block(pos):
    global woodcount, stoneblockcount, metalblockcount, flagcount, placedwood, placedstone, placedmetal, placedflagcount
    global obsidianblockcount, rugblockcount, placedobsidian, placedrug
    global placed_blocks
    x, y = pos
    for block in placed_blocks:
        if block["actor"].collidepoint(pos):
            img = block["actor"].image
            if img == "woodblock":
                woodcount += 1
                placedwood -= 1
            elif img == "stoneblock":
                stoneblockcount += 1
                placedstone -= 1
            elif img == "metalblock":
                metalblockcount += 1
                placedmetal -= 1
            elif img == "flag":
                flagcount += 1
                placedflagcount -= 1
            elif img == "obsidianblock":
                obsidianblockcount += 1
                placedobsidian -= 1
            elif img == "rugblock":
                rugblockcount += 1
                placedrug -= 1
            placed_blocks.remove(block)
            break
        
def restart_game():
    global number_of_rocks, money, sail_clicked_fun, music_playing, game_over
    global rock, treasurechest, placed_blocks, missed_rocks, rock2, meteor
    number_of_rocks = 0    
    sail_clicked_fun = False
    music_playing = False    
    missed_rocks = 0
    rock2.x = 1500  # Reset rock2 position
    rock.x = 1100 # Reset rock position  
    meteor.pos = mx, my  # Reset meteor position
    treasurechest.pos = (1600, 400)  # Reset treasure chest position
    save_game()  # Save the game state before restarting 
    music.stop() # type: ignore  # noqa: F821
    # Optionally reset block counts too:
    
def save_game():
    global woodcount, stoneblockcount, metalblockcount, flagcount, money, placedwood, placedstone, placedmetal, placedflagcount
    global obsidianblockcount, rugblockcount, placedobsidian, placedrug, level
    data = {
        "wood": woodcount + placedwood,
        "stone": stoneblockcount + placedstone,
        "metal": metalblockcount + placedmetal,
        "flag": flagcount + placedflagcount,
        "obsidian": obsidianblockcount + placedobsidian,
        "rug": rugblockcount + placedrug,
        # Save the current money
        "money": money,
        "level": level
    }
    with open("save_data.json", "w") as f:
        json.dump(data, f)

def load_game():
    global woodcount, stoneblockcount, metalblockcount, flagcount, money, load_game_once, placedwood, placedstone, placedmetal, placedflagcount
    global obsidianblockcount, rugblockcount, placedobsidian, placedrug, level    
    load_game_once = True
    try:
        with open("save_data.json", "r") as f:
            data = json.load(f)
            woodcount = data.get("wood", 0)
            stoneblockcount = data.get("stone", 0)
            metalblockcount = data.get("metal", 0)
            flagcount = data.get("flag", 0)
            obsidianblockcount = data.get("obsidian", 0)
            rugblockcount = data.get("rug", 0)
            money = data.get("money", 0)
            level = data.get("level", 0)
            
    except FileNotFoundError:
        pass  # No save file yet
        
    
def delete_save():
    try:
        os.remove("save_data.json")
        print("Save file deleted.")
    except FileNotFoundError:
        print("No save file to delete.")

def on_key_down(key):
    if key == keys.R:  # Press R to reset # type: ignore  # noqa: F821
        delete_save()

pgzrun.go()