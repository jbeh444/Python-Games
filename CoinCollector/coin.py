import pgzrun
from random import randint
WIDTH = 800
HEIGHT = 600
score = 0
game_over = False

fox = Actor("fox")
fox.pos = 100, 100

coin = Actor("treasure_chest")    
coin.pos = 200, 200

def draw():
    screen.fill("green")
    fox.draw()
    coin.draw()
    screen.draw.text("Score: " + str(score), color="black", topleft=(10,10))

    if game_over:
        screen.fill("purple")
        screen.draw.text("Final Score: " + str(score), topleft=(10,10), fontsize=60)

def place_coin():
    coin.x = randint(20, (WIDTH - 20))
    coin.y = randint(20, (HEIGHT -20))

def time_up():
    global game_over
    game_over = True

def update():
    global score
    speed = 12
    if keyboard.left:
        fox.x = fox.x - speed
    elif keyboard.right:
        fox.x = fox.x + speed
    elif keyboard.up:
        fox.y = fox.y - speed
    elif keyboard.down:
        fox.y = fox.y + speed

    coin_collected = fox.colliderect(coin)

    if coin_collected:
        score = score + 10
        place_coin()

clock.schedule(time_up, 15.0)
place_coin()
pgzrun.go()