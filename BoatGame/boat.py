import pgzrun
from random import randint

WIDTH = 1000
HEIGHT = 600

shop_items = {
    "wood": {"price": 50},
    "stone": {"price": 100},
    "metal": {"price": 500},
    "flag": {"price": 1000}
}

shop = Actor("shop")
shop.pos = 900, 300
sail = Actor("sail")
sail.pos = 900, 200
rock = Actor("rock")
rock.pos = 1600, randint(350, 550)
play = Actor("play")
play.pos = 500, 257
metalblock = Actor("metalblock")
metalblock.pos = 210, 250
stoneblock = Actor("stoneblock")
stoneblock.pos = 150, 250
woodblock = Actor("woodblock")
woodblock.pos = 90, 250 
treasurechest = Actor("tresurechest")
treasurechest.pos = 1600, 400
flag = Actor("flag")
flag.pos = 270, 250

sail_clicked_fun = False
music_playing = False
flagplaced = False
playing = False
number_of_rocks = 99
money = 0
woodcount = 5
stoneblockcount = 2
metalblockcount = 1
flagcount = 1
selected_block = None
placed_blocks = []

def draw():
    global sail_clicked_fun
    screen.blit("ocean", (0, 0))
    if playing:
        if sail_clicked_fun and music_playing: 
            if number_of_rocks >= 100:
                treasurechest.draw()      
            else:
                rock.draw()
            for block in placed_blocks:
                block["actor"].draw()

            screen.draw.text("Money: " + str(money), (500, 10), color="black")
        else:           
            #Drawing lines (Start position->(x.pos, y.pos), Stop position->(x.pos, y.pos), color)
            #Horizontal
            woodblock.draw()
            stoneblock.draw()
            metalblock.draw()
            flag.draw()
            for block in placed_blocks:
                block["actor"].draw()

            screen.draw.text("Money: " + str(money), (850, 520), color="black")
                     
            # Draw horizontal grid lines
            for y in range(286, 600, 60):
                screen.draw.line((0, y), (600, y), color="black")

            # Draw vertical grid lines
            for x in range(60, 601, 60):
                screen.draw.line((x, 286), (x, 586), color="black")

            # Build menu horizontal lines
            screen.draw.line((60, 220), (300, 220), color="black")
            screen.draw.line((60, 280), (300, 280), color="black")

            # Build menu vertical dividers
            for x in range(60, 301, 60):
                screen.draw.line((x, 220), (x, 280), color="black")
            
            # Draw block counts above the menu
            # Better-aligned block counts above the menu
            screen.draw.text("Wood: " + str(woodcount), (60, 200), color="black", fontsize=20)
            screen.draw.text("Stone: " + str(stoneblockcount), (125, 200), color="black", fontsize=20)
            screen.draw.text("Metal: " + str(metalblockcount), (190, 200), color="black", fontsize=20)
            screen.draw.text("Flag: " + str(flagcount), (255, 200), color="black", fontsize=20)


            
            sail.draw()
            shop.draw()
    else:
        play.draw()
    
def on_mouse_down(pos, button):
    global playing, selected_block
    if not playing or not sail_clicked_fun:  # 🔒 Only allow input before sailing
        if button == mouse.LEFT:
            if sail.collidepoint(pos):
                sail_clicked()
            elif shop.collidepoint(pos):
                open_shop_menu()
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
            else:
                place_block(pos)
        elif button == mouse.RIGHT:
            delete_block(pos)

def open_shop_menu():
    global money, woodcount, stoneblockcount, metalblockcount, flagcount
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
        
        
def sail_clicked():
    global sail_clicked_fun, music_playing

    # Prevent sailing if only a flag or no blocks
    non_flag_blocks = [b for b in placed_blocks if b["type"] != "flag"]
    if not non_flag_blocks:
        return  # Block sailing

    sail_clicked_fun = True
    if not music_playing:
        music.play("vanishing-horizon")
        music_playing = True

        
        
def update():
    global rock, number_of_rocks, treasurechest, sail_clicked_fun, money, music_playing, sail_clicked_fun
    global placed_blocks, flagplaced, flagcount, woodcount, stoneblockcount, metalblockcount
    if sail_clicked_fun:
        if rock.right > 0:        
            rock.x -= 5
            for block in placed_blocks[:]:
                if rock.colliderect(block["actor"]):
                    block["health"] -= 1
                    if block["health"] <= 0:
                        # Refill the count based on block type
                        if block["type"] == "wood":
                            woodcount += 1
                        elif block["type"] == "stone":
                            stoneblockcount += 1
                        elif block["type"] == "metal":
                            metalblockcount += 1
                        elif block["type"] == "flag":
                            flagcount += 1
                        placed_blocks.remove(block)
                    # Rock hit something, reset
                    rock.x = 1600
                    rock.y = randint(350, 550)
                    number_of_rocks += 1
                    money += 8
                    break
        else:
            # Rock missed everything, still reset!
            rock.x = 1600
            rock.y = randint(350, 550)
            number_of_rocks += 1
            money += 8

         # Check if the flag is broken
        flag_broken = not any(block["type"] == "flag" for block in placed_blocks)

        # Check if no blocks are left
        no_blocks_left = len(placed_blocks) == 0

        if flag_broken or no_blocks_left:
            restart_game()  

        if number_of_rocks >= 100:
            if treasurechest.right > 0:
                treasurechest.x -= 5
                for block in placed_blocks[:]:
                    if treasurechest.colliderect(block["actor"]) or treasurechest.x < 0:
                        money += 1000
                        treasurechest.pos = (-200, 400)
                        restart_game()
                        break  # Important: stop checking once you've found a collision
    


def place_block(pos):
    global selected_block, woodcount, stoneblockcount, metalblockcount, flagcount
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
                new_block = Actor("woodblock")
                woodcount -= 1
            elif selected_block == "stone" and stoneblockcount > 0:
                new_block = Actor("stoneblock")
                stoneblockcount -= 1
            elif selected_block == "metal" and metalblockcount > 0:
                new_block = Actor("metalblock")
                metalblockcount -= 1
            elif selected_block == "flag" and flagcount > 0:
                new_block = Actor("flag")
                flagcount -= 1

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

                placed_blocks.append({
                    "actor": new_block,
                    "type": selected_block,  # ← Add this line
                    "health": health
                })

def delete_block(pos):
    global woodcount, stoneblockcount, metalblockcount, flagcount
    x, y = pos
    for block in placed_blocks:
        if block["actor"].collidepoint(pos):
            img = block["actor"].image
            if img == "woodblock":
                woodcount += 1
            elif img == "stoneblock":
                stoneblockcount += 1
            elif img == "metalblock":
                metalblockcount += 1
            elif img == "flag":
                flagcount += 1
            placed_blocks.remove(block)
            break
def restart_game():
    global number_of_rocks, money, sail_clicked_fun, music_playing, game_over
    global rock, treasurechest, placed_blocks
    number_of_rocks = 0    
    sail_clicked_fun = False
    music_playing = False       
    music.stop()
    # Optionally reset block counts too:
    


pgzrun.go()