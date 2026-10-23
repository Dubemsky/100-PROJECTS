import math
import random
import tkinter as tk
import customtkinter as ctk

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Table Tennis")
app.configure(fg_color="#eef0f8")
app.resizable(False, False)

ACCENT_COLOR = "#4f46e5"
ACCENT_HOVER = "#4338ca"
TINT_COLOR = "#f3f4fd"
TINT_BORDER = "#e3e6fb"

TABLE_WIDTH = 800
TABLE_HEIGHT = 480
TABLE_COLOR = "#1e3a8a"
LINE_COLOR = "#ffffff"
BALL_COLOR = "#fb923c"
PLAYER_COLOR = "#dc2626"
COMPUTER_COLOR = "#111827"

PADDLE_WIDTH = 14
PADDLE_HEIGHT = 90
PADDLE_MARGIN = 30
PADDLE_SPEED = 7

BALL_RADIUS = 10
BALL_START_SPEED = 6
BALL_MAX_SPEED = 14
BALL_SPEEDUP = 1.05
MAX_BOUNCE_ANGLE = math.radians(55)

COMPUTER_SPEED = 4.6
COMPUTER_DEADZONE = 10
COMPUTER_MAX_ERROR = 35

WINNING_SCORE = 7
SERVE_DELAY_FRAMES = 50
FRAME_DELAY = 16
TRAIL_LENGTH = 8

player_y = TABLE_HEIGHT / 2
computer_y = TABLE_HEIGHT / 2
ball_x = TABLE_WIDTH / 2
ball_y = TABLE_HEIGHT / 2
ball_vx = 0
ball_vy = 0
ball_speed = BALL_START_SPEED
ball_trail = []
player_score = 0
computer_score = 0
computer_aim_error = 0
serve_delay = 0
keys_down = set()
is_playing = False
is_paused = False
game_loop_id = None
game_mode = "computer"


# mixes two hex colors together, amount 0 gives color_a and 1 gives color_b
def blend_colors(color_a, color_b, amount):
    a = [int(color_a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(color_b[i:i + 2], 16) for i in (1, 3, 5)]
    mixed = [round(a[i] + (b[i] - a[i]) * amount) for i in range(3)]
    return "#{:02x}{:02x}{:02x}".format(*mixed)


# draws a rectangle with rounded corners on the canvas (tkinter has no built in one)
def draw_rounded_rect(x1, y1, x2, y2, radius, **options):
    points = [
        x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
        x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2,
        x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **options)


# puts the ball in the middle and serves it towards the given side (-1 = left, 1 = right)
def serve_ball(direction):
    global ball_x, ball_y, ball_vx, ball_vy, ball_speed, ball_trail, serve_delay
    ball_x = TABLE_WIDTH / 2
    ball_y = TABLE_HEIGHT / 2
    ball_speed = BALL_START_SPEED
    ball_trail = []
    angle = random.uniform(-0.4, 0.4)
    ball_vx = direction * ball_speed * math.cos(angle)
    ball_vy = ball_speed * math.sin(angle)
    serve_delay = SERVE_DELAY_FRAMES


# moves player 1's paddle up or down; in computer mode the arrow keys work too since nothing else uses them
def move_player():
    global player_y
    up_keys = {"w"} if game_mode == "human" else {"w", "up"}
    down_keys = {"s"} if game_mode == "human" else {"s", "down"}
    if keys_down & up_keys:
        player_y -= PADDLE_SPEED
    if keys_down & down_keys:
        player_y += PADDLE_SPEED
    player_y = max(PADDLE_HEIGHT / 2, min(TABLE_HEIGHT - PADDLE_HEIGHT / 2, player_y))


# moves player 2's paddle with the arrow keys, only used in human vs human mode
def move_player_two():
    global computer_y
    if "up" in keys_down:
        computer_y -= PADDLE_SPEED
    if "down" in keys_down:
        computer_y += PADDLE_SPEED
    computer_y = max(PADDLE_HEIGHT / 2, min(TABLE_HEIGHT - PADDLE_HEIGHT / 2, computer_y))


# moves the computer's paddle towards the ball, but only when the ball is heading its way
# the aim error makes it miss a little so the computer can be beaten
def move_computer():
    global computer_y
    target = ball_y + computer_aim_error if ball_vx > 0 else TABLE_HEIGHT / 2
    difference = target - computer_y
    if abs(difference) > COMPUTER_DEADZONE:
        step = min(COMPUTER_SPEED, abs(difference))
        computer_y += step if difference > 0 else -step
    computer_y = max(PADDLE_HEIGHT / 2, min(TABLE_HEIGHT - PADDLE_HEIGHT / 2, computer_y))


# bounces the ball off a paddle: hitting near the edge sends it at a steeper angle, and every hit speeds it up
def bounce_off_paddle(paddle_y, direction):
    global ball_vx, ball_vy, ball_speed
    offset = (ball_y - paddle_y) / (PADDLE_HEIGHT / 2)
    offset = max(-1, min(1, offset))
    angle = offset * MAX_BOUNCE_ANGLE
    ball_speed = min(BALL_MAX_SPEED, ball_speed * BALL_SPEEDUP)
    ball_vx = direction * ball_speed * math.cos(angle)
    ball_vy = ball_speed * math.sin(angle)


# checks whether the ball is touching either paddle and bounces it back if so
def check_paddle_hits():
    global ball_x, computer_aim_error
    player_right = PADDLE_MARGIN + PADDLE_WIDTH
    computer_left = TABLE_WIDTH - PADDLE_MARGIN - PADDLE_WIDTH

    if ball_vx < 0 and PADDLE_MARGIN <= ball_x - BALL_RADIUS <= player_right:
        if abs(ball_y - player_y) <= PADDLE_HEIGHT / 2 + BALL_RADIUS:
            ball_x = player_right + BALL_RADIUS
            bounce_off_paddle(player_y, 1)
            computer_aim_error = random.randint(-COMPUTER_MAX_ERROR, COMPUTER_MAX_ERROR)

    if ball_vx > 0 and computer_left <= ball_x + BALL_RADIUS <= computer_left + PADDLE_WIDTH:
        if abs(ball_y - computer_y) <= PADDLE_HEIGHT / 2 + BALL_RADIUS:
            ball_x = computer_left - BALL_RADIUS
            bounce_off_paddle(computer_y, -1)


# gives a point to whoever the ball got past, then serves again or ends the game
def score_point(player_won_point):
    global player_score, computer_score
    if player_won_point:
        player_score += 1
        serve_ball(1)
    else:
        computer_score += 1
        serve_ball(-1)

    if player_score >= WINNING_SCORE or computer_score >= WINNING_SCORE:
        end_game()


# moves the ball one frame: wall bounces, paddle hits and scoring
def move_ball():
    global ball_x, ball_y, ball_vy
    ball_trail.append((ball_x, ball_y))
    if len(ball_trail) > TRAIL_LENGTH:
        ball_trail.pop(0)

    ball_x += ball_vx
    ball_y += ball_vy

    if ball_y - BALL_RADIUS <= 0:
        ball_y = BALL_RADIUS
        ball_vy = abs(ball_vy)
    elif ball_y + BALL_RADIUS >= TABLE_HEIGHT:
        ball_y = TABLE_HEIGHT - BALL_RADIUS
        ball_vy = -abs(ball_vy)

    check_paddle_hits()

    if ball_x + BALL_RADIUS < 0:
        score_point(False)
    elif ball_x - BALL_RADIUS > TABLE_WIDTH:
        score_point(True)


# draws the table, net, scores, ball trail, ball and both paddles
def draw_game():
    canvas.delete("all")
    canvas.create_rectangle(0, 0, TABLE_WIDTH, TABLE_HEIGHT, fill=TABLE_COLOR, outline="")
    canvas.create_rectangle(8, 8, TABLE_WIDTH - 8, TABLE_HEIGHT - 8, outline=LINE_COLOR, width=3)
    canvas.create_line(TABLE_WIDTH / 2, 8, TABLE_WIDTH / 2, TABLE_HEIGHT - 8, fill=LINE_COLOR, width=3, dash=(12, 10))

    left_name, right_name = ("PLAYER 1", "PLAYER 2") if game_mode == "human" else ("YOU", "COMPUTER")

    score_font = ("Helvetica", 56, "bold")
    canvas.create_text(TABLE_WIDTH / 2 - 90, 70, text=str(player_score), fill=LINE_COLOR, font=score_font)
    canvas.create_text(TABLE_WIDTH / 2 + 90, 70, text=str(computer_score), fill=LINE_COLOR, font=score_font)
    canvas.create_text(TABLE_WIDTH / 2 - 90, 118, text=left_name, fill="#93c5fd", font=("Helvetica", 12, "bold"))
    canvas.create_text(TABLE_WIDTH / 2 + 90, 118, text=right_name, fill="#93c5fd", font=("Helvetica", 12, "bold"))

    for index, (trail_x, trail_y) in enumerate(ball_trail):
        fade = (index + 1) / (TRAIL_LENGTH + 1)
        size = BALL_RADIUS * (0.4 + 0.5 * fade)
        color = blend_colors(TABLE_COLOR, BALL_COLOR, fade * 0.7)
        canvas.create_oval(trail_x - size, trail_y - size, trail_x + size, trail_y + size, fill=color, outline="")

    canvas.create_oval(ball_x - BALL_RADIUS, ball_y - BALL_RADIUS, ball_x + BALL_RADIUS, ball_y + BALL_RADIUS, fill=BALL_COLOR, outline="")
    canvas.create_oval(ball_x - 5, ball_y - 6, ball_x - 1, ball_y - 2, fill="#fed7aa", outline="")

    player_x = PADDLE_MARGIN
    computer_x = TABLE_WIDTH - PADDLE_MARGIN - PADDLE_WIDTH
    draw_rounded_rect(player_x, player_y - PADDLE_HEIGHT / 2, player_x + PADDLE_WIDTH, player_y + PADDLE_HEIGHT / 2, 6, fill=PLAYER_COLOR, outline="#fca5a5", width=2)
    draw_rounded_rect(computer_x, computer_y - PADDLE_HEIGHT / 2, computer_x + PADDLE_WIDTH, computer_y + PADDLE_HEIGHT / 2, 6, fill=COMPUTER_COLOR, outline="#9ca3af", width=2)

    if is_paused:
        canvas.create_text(TABLE_WIDTH / 2, TABLE_HEIGHT / 2, text="PAUSED", fill=LINE_COLOR, font=("Helvetica", 44, "bold"))


# runs once per frame: moves everything, then draws it and schedules the next frame
def game_loop():
    global serve_delay, game_loop_id
    if not is_playing:
        return

    if not is_paused:
        move_player()
        if game_mode == "human":
            move_player_two()
        else:
            move_computer()
        if serve_delay > 0:
            serve_delay -= 1
        else:
            move_ball()

    draw_game()
    if is_playing:
        game_loop_id = app.after(FRAME_DELAY, game_loop)


# stops the game loop and shows the winner with Play Again and Menu buttons
def end_game():
    global is_playing
    is_playing = False
    left_name, right_name = ("Player 1", "Player 2") if game_mode == "human" else ("You", "Computer")
    winner_label.configure(text=f"{left_name} wins!" if player_score > computer_score else f"{right_name} wins!")
    final_score_label.configure(text=f"{player_score} - {computer_score}")
    result_frame.place(relx=0.5, rely=0.5, anchor="center")


# resets scores and positions, then starts a fresh game in the given mode ("computer" or "human")
def start_game(mode):
    global player_score, computer_score, player_y, computer_y, is_playing, is_paused, game_loop_id, game_mode
    if game_loop_id is not None:
        app.after_cancel(game_loop_id)
    game_mode = mode
    player_score = 0
    computer_score = 0
    player_y = TABLE_HEIGHT / 2
    computer_y = TABLE_HEIGHT / 2
    is_paused = False
    is_playing = True
    keys_down.clear()
    serve_ball(random.choice([-1, 1]))
    result_frame.place_forget()
    menu_frame.pack_forget()
    game_frame.pack(padx=30, pady=30)
    pause_button.configure(text="Pause")
    controls_label.configure(
        text="Player 1: W / S      Player 2: Up / Down arrows" if mode == "human" else "W / S or arrow keys to move"
    )
    game_loop()


# stops the game and goes back to the start screen
def show_menu():
    global is_playing
    is_playing = False
    result_frame.place_forget()
    game_frame.pack_forget()
    menu_frame.pack(padx=30, pady=30)


# pauses or resumes the game
def toggle_pause():
    global is_paused
    if not is_playing:
        return
    is_paused = not is_paused
    pause_button.configure(text="Resume" if is_paused else "Pause")


# remembers which keys are currently held down
def on_key_press(event):
    key = event.keysym.lower()
    if key == "space":
        toggle_pause()
    else:
        keys_down.add(key)


# forgets a key once it is let go
def on_key_release(event):
    keys_down.discard(event.keysym.lower())


# start screen
menu_frame = ctk.CTkFrame(app, fg_color="white", corner_radius=24, border_width=1, border_color=TINT_BORDER)
menu_frame.pack(padx=30, pady=30)

ctk.CTkLabel(menu_frame, text="Table Tennis", font=("Georgia", 40, "bold"), text_color="#1e1b3a").pack(padx=120, pady=(50, 4))
ctk.CTkLabel(menu_frame, text=f"First to {WINNING_SCORE} points wins", font=("Helvetica", 15), text_color="#8a88a8").pack()

ctk.CTkButton(
    menu_frame, text="Play vs Computer", command=lambda: start_game("computer"), width=280, height=54,
    font=("Helvetica", 18, "bold"), corner_radius=14, fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER,
).pack(pady=(40, 12))

ctk.CTkButton(
    menu_frame, text="Play vs Human", command=lambda: start_game("human"), width=280, height=54,
    font=("Helvetica", 16, "bold"), corner_radius=14, fg_color=TINT_COLOR, text_color="#1e1b3a", hover_color=TINT_BORDER,
    border_width=1, border_color=TINT_BORDER,
).pack(pady=(0, 24))

ctk.CTkLabel(
    menu_frame,
    text="Vs Computer: W / S or arrow keys\nVs Human: Player 1 uses W / S, Player 2 uses arrow keys\nSpace pauses the game",
    font=("Helvetica", 13), text_color="#8a88a8", justify="center",
).pack(pady=(0, 44))

# game screen
game_frame = ctk.CTkFrame(app, fg_color="transparent")

canvas = tk.Canvas(game_frame, width=TABLE_WIDTH, height=TABLE_HEIGHT, highlightthickness=0, bg=TABLE_COLOR)
canvas.pack()

button_row = ctk.CTkFrame(game_frame, fg_color="transparent")
button_row.pack(fill="x", pady=(14, 0))

pause_button = ctk.CTkButton(
    button_row, text="Pause", command=toggle_pause, width=110, height=38, corner_radius=12,
    fg_color=TINT_COLOR, text_color="#1e1b3a", hover_color=TINT_BORDER, border_width=1, border_color=TINT_BORDER,
)
pause_button.pack(side="left")

controls_label = ctk.CTkLabel(button_row, text="W / S or arrow keys to move", font=("Helvetica", 13), text_color="#8a88a8")
controls_label.pack(side="left", padx=20)

ctk.CTkButton(
    button_row, text="Menu", command=show_menu, width=110, height=38, corner_radius=12,
    fg_color=TINT_COLOR, text_color="#1e1b3a", hover_color=TINT_BORDER, border_width=1, border_color=TINT_BORDER,
).pack(side="right")

# game over box, shown on top of the table
result_frame = ctk.CTkFrame(game_frame, fg_color="white", bg_color=TABLE_COLOR, corner_radius=20, border_width=1, border_color=TINT_BORDER)

winner_label = ctk.CTkLabel(result_frame, text="", font=("Georgia", 34, "bold"), text_color="#1e1b3a")
winner_label.pack(padx=70, pady=(30, 0))

final_score_label = ctk.CTkLabel(result_frame, text="", font=("Helvetica", 22, "bold"), text_color=ACCENT_COLOR)
final_score_label.pack(pady=(4, 18))

ctk.CTkButton(
    result_frame, text="Play Again", command=lambda: start_game(game_mode), width=200, height=46, corner_radius=12,
    font=("Helvetica", 16, "bold"), fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER,
).pack(pady=(0, 10))

ctk.CTkButton(
    result_frame, text="Menu", command=show_menu, width=200, height=40, corner_radius=12,
    fg_color=TINT_COLOR, text_color="#1e1b3a", hover_color=TINT_BORDER, border_width=1, border_color=TINT_BORDER,
).pack(pady=(0, 28))

app.bind("<KeyPress>", on_key_press)
app.bind("<KeyRelease>", on_key_release)

app.mainloop()
