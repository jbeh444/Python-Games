import pgzrun
from random import randint

WIDTH = 1000
HEIGHT = 575

shop = Actor("shop")
shop.pos = 900, 300
sail = Actor("sail")
sail.pos = 900, 200
rock = Actor("rock")
rock.pos = 1600, 400
play = Actor("play")
play.pos = 500, 257
metalblock = Actor("metalblock")
stoneblock = Actor("stoneblock")
woodblock = Actor("woodblock") 
treasurechest = Actor("tresurechest")
flag = Actor("flag")
game_over = False
sail_clicked_fun = False
music_playing = False
flagplaced = False
playing = False
number_of_rocks = 0


def draw():
    global sail_clicked_fun
    screen.blit("ocean", (0, 0))
    if playing:
        if sail_clicked_fun and music_playing:        
            rock.draw()
        else:
            sail.draw()
            shop.draw()
    else:
        play.draw()
    
def on_mouse_down(pos):  
    global playing, game_over 
    if sail.collidepoint(pos): 
        sail_clicked()
    if play.collidepoint(pos) and not sail_clicked_fun:        
        playing = True
        buildmode()
         
def sail_clicked():
    global sail_clicked_fun, music_playing        
    sail_clicked_fun = True
    if not music_playing:
        music.play("vanishing-horizon")
        music_playing = True
        
        
def update():
    global rock, metalblock, stoneblock, woodblock, treasurechest, flag, number_of_rocks, sail_clicked_fun
    if not game_over and sail_clicked_fun:
        if rock.right > 0:        
            rock.x -= 5
        else:
            rock.x = 1600
            rock.y = 400
            number_of_rocks += 1
        
def buildmode():
    global metalblock, stoneblock, woodblock, treasurechest, flag, playing
    metalblock.pos = 100, 400
    stoneblock.pos = 300, 400
    woodblock.pos = 500, 400
    treasurechest.pos = 700, 400
    flag.pos = 900, 400
   
    
            
pgzrun.go()