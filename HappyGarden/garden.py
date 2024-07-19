import pgzrun
from random import randint
import time

WIDTH = 800
HEIGHT = 600
CENTER_X = WIDTH / 2
CENTER_Y = HEIGHT / 2

game_over = False
finalized = False
raining = False
garden_happy = True
fangflower_collision = False
time_elapsed = 0
start_time = int(time.time())
cow = Actor('cow')
cow.pos = (100, 500)
flower_list = []
wilted_list = []
fang_flower_list = []
fangflower_vy_list = []
fangflower_vx_list = []

def draw():
    global game_over, time_elapsed, finalized
    if not game_over:
        screen.clear()
        if not raining:
            screen.blit('garden', (0, 0))
        else:
            screen.blit('garden-raining', (0, 0))
        cow.draw()
        for flower in flower_list:
            flower.draw()
        for fangflower in fang_flower_list:
            fangflower.draw()
        time_elapsed =  int(time.time()) - start_time
        screen.draw.text("Garden happy for: " + str(time_elapsed) + " seconds", topleft =(10, 10), color="black")
    else:
        if not finalized:
            cow.draw()
            screen.draw.text("Garden happy for: " + str(time_elapsed) + " seconds", topleft =(10, 10), color="black")
            if not garden_happy:
                screen.draw.text("GARDEN UNHAPPY-GAME OVER!", topleft =(10, 50), color="black")                
                finalized = True
            else:
                screen.draw.text("FANGFLOWER ATTACK-GAME OVER!: " , topleft =(10, 50), color="black")
                finalized = True
            music.stop()
    return

def new_flower():
    global flower_list, wilted_list
    flower_new = Actor('flower')
    flower_new.pos = randint(80, WIDTH - 80), randint(200, HEIGHT - 125)
    flower_list.append(flower_new)
    wilted_list.append("happy")
    return

def add_flowers():
    global game_over
    if not game_over:
        new_flower()
        clock.schedule(add_flowers, 4)
    return

def wilt_flowers():
    global flower_list, wilted_list, game_over
    if not game_over and not raining:
        if flower_list:
            rand_flower = randint(0, len(flower_list) - 1)  
            if flower_list[rand_flower].image == 'flower':
                flower_list[rand_flower].image = 'flower-wilt'
                wilted_list[rand_flower] = time.time()
        clock.schedule(wilt_flowers, 3)
    return

def check_wilt_times():
    global wilted_list, game_over, garden_happy
    if wilted_list:
        for wilted_since in wilted_list:
            if wilted_since != "happy":
                time_wilted = int(time.time()) - wilted_since
                if time_wilted > 10.0:
                    game_over = True
                    garden_happy = False
                    break 
    return

def check_flower_collision():
    global cow, flower_list, wilted_list
    index = 0
    for flower in flower_list:
        if cow.colliderect(flower) and flower.image == 'flower-wilt':
            flower.image = 'flower'
            wilted_list[index] = "happy"
            break
        index += 1
    return

def check_fangflower_collision():
    global cow, fang_flower_list, fangflower_collision, game_over    
    for fangflower in fang_flower_list:
        if fangflower.colliderect(cow):
            cow.image = "zap"
            game_over = True            
            break        
    return

def mutate():
    global fang_flower_list, fangflower_vx_list, fangflower_vy_list, game_over
    if not game_over and flower_list:
        rand_flower = randint(0, len(flower_list) - 1)
        fangflower_pos_x = flower_list[rand_flower].x
        fangflower_pos_y = flower_list[rand_flower].y
        del flower_list[rand_flower]
        fang_flower = Actor('fangflower')
        fang_flower.pos = (fangflower_pos_x, fangflower_pos_y)
        fangflower_vx = velocity()
        fangflower_vy = velocity()
        fang_flower_list.append(fang_flower)
        fangflower_vx_list.append(fangflower_vx)
        fangflower_vy_list.append(fangflower_vy)
        clock.schedule(mutate, 20)
    return

def velocity():
    random_dir = randint(0, 1)
    randon_velocity = randint(2, 3)
    if random_dir == 0:
        return -randon_velocity
    else:
        return randon_velocity

def update_fangflowers():
    global fang_flower_list, game_over
    if not game_over:
        index = 0
        for fangflower in fang_flower_list:
            fangflower_vx = fangflower_vx_list[index]
            fangflower_vy = fangflower_vy_list[index]
            fangflower.x += fangflower_vx
            fangflower.y += fangflower_vy
            if fangflower.left < 0:                
                fangflower_vx_list[index] = -fangflower_vx
            if fangflower.right > WIDTH:
                fangflower_vx_list[index] = -fangflower_vx    
            if fangflower.top < 170:
                fangflower_vy_list[index] = -fangflower_vy
            if fangflower.bottom > HEIGHT - 125:
                fangflower_vy_list[index] = -fangflower_vy
            index += 1
    return

def reset_cow():
    global game_over
    if not game_over:
        cow.image = 'cow'
    return

add_flowers()
wilt_flowers()
music.play("vanishing-horizon")

def update():
    global score, game_over, fangflower_collision, flower_list, fang_flower_list, time_elapsed, finalized, garden_happy, raining
    fangflower_collision = check_fangflower_collision()
    check_wilt_times()
    if not game_over:
        if keyboard.space:
            cow.image = 'cow-water'
            clock.schedule(reset_cow, 0.5)
            check_flower_collision()
        if keyboard.left and cow.x > 30:
            cow.x -= 5
        elif keyboard.right and cow.x < WIDTH:
            cow.x += 5
        elif keyboard.up and cow.y > 150:
            cow.y -= 5
        elif keyboard.down and cow.y < HEIGHT:
            cow.y += 5
        if time_elapsed > 20 and not fang_flower_list:
            mutate()
        update_fangflowers()
        if time_elapsed > 20:
            raining = True
    # else:
    #     if game_over and keyboard.space:            
    #         game_over = False
    #         finalized = False
    #         garden_happy = True
pgzrun.go()