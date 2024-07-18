import pgzrun
from pgzero.builtins import Actor, animate, keyboard
from random import randint

WIDTH = 500
HEIGHT = 500
game_over = False

dots = []
lines = []

number_of_dots = 10

next_dot = 0

for dot in range(0, number_of_dots):
    actor = Actor("dot.png")
    actor.pos = randint(20, WIDTH -20), \
    randint (20, HEIGHT - 20)
    dots.append(actor)

def draw():    
    screen.fill("black")
    number = 1
    for dot in dots:
        screen.draw.text(str(number), \
        (dot.pos[0], dot.pos[1] + 12))
        dot.draw()
        number += 1
    for line in lines:
        screen.draw.line(line[0], line[1], (0, 0, 100))

# def next_level():
#     if next_dot == number_of_dots-1:
#         lines = []
#         for dot in dots:
#             x = randint(20, WIDTH - 20)
#             y = randint(20, HEIGHT - 20)
#             dot.pos = x, y
#         next_dot = 0

def on_mouse_down(pos):
    global next_dot
    global lines
    if next_dot == len(dots):
            next_dot = 0
            lines = []
            game_over = True
    if dots[next_dot].collidepoint(pos):
        if next_dot:
            lines.append((dots[next_dot - 1].pos, dots[next_dot].pos))
        next_dot += 1        
    else:
        next_dot = 0
        lines = []
        # next_level()

pgzrun.go()