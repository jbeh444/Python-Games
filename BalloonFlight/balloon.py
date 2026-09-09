import os
from pathlib import Path
from random import randint
import pgzrun

WIDTH = 800
HEIGHT = 600

balloon = Actor("balloon")  # type: ignore  # noqa: F821
balloon.pos = 400, 300

bird = Actor("bird-up")  # type: ignore  # noqa: F821
bird.pos = randint(800, 1600), randint(10, 100)

house = Actor("house")  # type: ignore  # noqa: F821
house.pos = randint(800, 1600), 460

tree = Actor("tree")  # type: ignore  # noqa: F821
tree.pos = randint(800, 1600), 450

bird_up = True
up = False
game_over = False
score = 0
number_of_updates = 0
music.play("vanishing-horizon")  # type: ignore  # noqa: F821

scores = []


def update_high_scores():
    global score, scores
    # Automatically locate high-scores.txt relative to balloon.py
    filename = Path(__file__).parent / "high-scores.txt"

    # Create file with default scores if it doesn't exist yet
    if not filename.exists():
        filename.write_text("10 8 6 4 2")

    scores = []
    with open(filename, "r") as file:
        line = file.readline()
        high_scores = line.split()

    for high_score in high_scores:
        if score > int(high_score):
            scores.append(str(score) + " ")
            score = int(high_score)
        else:
            scores.append(str(high_score) + " ")

    with open(filename, "w") as file:
        for high_score in scores:
            file.write(high_score)


def display_high_scores():
    screen.draw.text("HIGH SCORES", (350, 150), color="black")  # type: ignore  # noqa: F821
    y = 175
    position = 1
    for high_score in scores:
        screen.draw.text(str(position) + ". " + high_score, (350, y), color="black")  # type: ignore  # noqa: F821
        y += 25
        position += 1
    screen.draw.text("Press spacebar to play again", (350, y + 25), color="black")  # type: ignore  # noqa: F821


def draw():
    screen.blit("background", (0, 0))  # type: ignore  # noqa: F821
    if not game_over:
        balloon.draw()
        bird.draw()
        house.draw()
        tree.draw()
        screen.draw.text("Score: " + str(score), (700, 10), color="black")  # type: ignore  # noqa: F821
    else:
        display_high_scores()


def on_mouse_down(pos):
    global up
    up = True
    balloon.y -= 40


def on_mouse_up():
    global up
    up = False


def flap():
    global bird_up
    if bird_up:
        bird.image = "bird-down"
        bird_up = False
    else:
        bird.image = "bird-up"
        bird_up = True


def update():
    global game_over, score, number_of_updates

    if not game_over:
        if not up:
            balloon.y += 1
        if bird.x > 0:
            bird.x -= 4
            if number_of_updates == 9:
                flap()
                number_of_updates = 0
            else:
                number_of_updates += 1
        else:
            bird.x = randint(800, 1600)
            bird.y = randint(10, 100)
            score += 1
            number_of_updates = 0

        if house.right > 0:
            house.x -= 2
        else:
            house.x = randint(800, 1600)
            score += 1

        if tree.right > 0:
            tree.x -= 2
        else:
            tree.x = randint(800, 1600)
            score += 1

        # Check for game over triggers
        if (
            balloon.top < 0
            or balloon.bottom > 560
            or balloon.collidepoint(bird.x, bird.y)
            or balloon.collidepoint(house.x, house.y)
            or balloon.collidepoint(tree.x, tree.y)
        ):
            game_over = True
            update_high_scores()  # Called EXACTLY ONCE on collision

    elif keyboard.space:  # type: ignore  # noqa: F821
        game_over = False
        score = 0
        balloon.pos = 400, 300
        bird.pos = randint(800, 1600), randint(10, 100)
        house.pos = randint(800, 1600), 460
        tree.pos = randint(800, 1600), 450
        number_of_updates = 0
        scores = []
        music.play("vanishing-horizon")  # type: ignore  # noqa: F821


pgzrun.go()