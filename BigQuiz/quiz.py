import pgzrun

WIDTH = 1280
HEIGHT = 720

main_box = Rect(0, 0, 820, 240)
timer_box = Rect(0, 0, 240, 240)
answer_box1 = Rect(0, 0, 495, 165)
answer_box2 = Rect(0, 0, 495, 165)
answer_box3 = Rect(0, 0, 495, 165)
answer_box4 = Rect(0, 0, 495, 165)

main_box.move_ip(50, 40)
timer_box.move_ip(990, 40)
answer_box1.move_ip(50, 358)
answer_box2.move_ip(735, 358)
answer_box3.move_ip(50, 538)
answer_box4.move_ip(735, 538)

answer_boxes = [answer_box1, answer_box2, answer_box3, answer_box4]

score = 0

time_left = 10

q1 = ["What is the capital of France?", "London","Paris", "Berlin","Tokyo", 2] #The last number in the list indicates the correct answer
q2 = ["What is 5 + 7?", "10", "12", "13", "14", 2]
q3 = ["What is the capital of Italy?", "London", "Rome", "Berlin", "Madrid", 2]
q4 = ["What is 4 x 3?", "8", "12", "14", "16", 2]
q5 = ["What is the capital of Spain?", "London", "Paris", "Berlin", "Madrid", 4]
q6 = ["What is 8 + 7?", "10", "12", "13", "15", 4]
q7 = ["What is the capital of Portugal?", "Lisbon", "Paris", "Berlin", "Madrid", 1]
q8 = ["What is 6 x 7?", "42", "44", "46", "48", 1]
q9 = ["What is the capital of Germany?", "London", "Paris", "Berlin", "Madrid", 3]
q10 = ["What is 9 + 6?", "10", "12", "13", "15", 4]

questions = [q1, q2, q3, q4, q5, q6, q7, q8, q9, q10]
question = questions.pop(0)
def draw():
    screen.fill("dim grey")
    screen.draw.filled_rect(main_box, "sky blue")
    screen.draw.filled_rect(timer_box, "sky blue")

    for box in answer_boxes:
      screen.draw.filled_rect(box, "orange")

    screen.draw.textbox(str(time_left), timer_box, color=("black"))
    screen.draw.textbox(question[0],main_box, color=("black"))

    index = 1
    for box in answer_boxes:
        screen.draw.textbox(question[index],box, color=("black"))
        index +=1
def game_over():
    global question, time_left
    message = "Game over. You got %s questions correct" %str(score)
    question = [message, "-","-","-","-",5]
    time_left = 0

def correct_answer():
    global question, score, time_left
    score +=1
    if questions:
        question = questions.pop(0)
        time_left = 10
    else:
        print("End of questions")   
        game_over()
        
def on_mouse_down(pos):
    index = 1
    for box in answer_boxes:
        if box.collidepoint(pos):
            print("Clicked on answer " + str(index))
            if index == question[5]:
                print("You got it correct!")
                correct_answer()
            else:
                game_over()
        index+=1

def update_time_left():
    global time_left
    if time_left:
        time_left -=1
    else:
        game_over()

clock.schedule_interval(update_time_left,1.0)
pgzrun.go()