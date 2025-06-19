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
metalBlock = Actor("metalblock")
stoneBlock = Actor("stoneblock")
woodBlock = Actor("woodblock") 
treasurechest = Actor("tresurechest")
flag = Actor("flag")
game_over = False
sail_clicked_fun = False
music_playing = False
flagplaced = False
playing = False

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
        
         
def sail_clicked():
    global sail_clicked_fun, music_playing        
    sail_clicked_fun = True
    if not music_playing:
        music.play("vanishing-horizon")
        music_playing = True
        
def update():
    global rock, metalBlock, stoneBlock, woodBlock, treasurechest, flag
    if not game_over:
        if rock.x > 0:        
            rock.x -= 5
        else:
            rock.x = 1600
            rock.y = 400
        
        
pgzrun.go()