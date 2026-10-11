import math
import random
from PIL import Image, ImageDraw
import customtkinter as ctk

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Tic Tac Toe")
app.configure(fg_color="#2e1b0e")

BOX_COLOR = "#4a2c17"
BOX_BORDER_COLOR = "#2e1b0e"
CREAM = "#f4e4c1"
TILE_BASE_COLOR = "#d1a06c"
TILE_GRAIN_COLOR = "#b0804f"
WIN_TILE_COLOR = "#e3b04b"
WIN_LINE_COLOR = "#c0392b"

WIN_COMBOS = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
]

tile_images = []
cell_buttons = []
board = [None] * 9
current_player = "X"
x_score = 0
o_score = 0
draw_score = 0


# procedurally draws a wood-grain tile: a base color with smooth wavy streaks of a darker tone
def generate_wood_texture(width, height, base_color, grain_color, grain_count=8):
    image = Image.new("RGB", (width, height), base_color)
    draw = ImageDraw.Draw(image)

    for _ in range(grain_count):
        base_y = random.randint(0, height)
        thickness = random.choice([1, 1, 2])
        amplitude = random.uniform(1, 3)
        phase = random.uniform(0, math.pi * 2)

        points = []
        for x in range(0, width + 1, 4):
            y = base_y + amplitude * math.sin((x / width) * math.pi * 2 + phase)
            points.append((x, y))

        draw.line(points, fill=grain_color, width=thickness, joint="curve")

    return image


# builds one wood tile as a CTkImage, ready to use as a button's image
def make_tile_image(size=100):
    texture = generate_wood_texture(size, size, TILE_BASE_COLOR, TILE_GRAIN_COLOR)
    tile_image = ctk.CTkImage(light_image=texture, dark_image=texture, size=(size, size))
    tile_images.append(tile_image)
    return tile_image


# draws the segment of the winning line that crosses this tile, so it lines up across the row/column/diagonal
def draw_win_line_segment(draw, size, winning_combo):
    if winning_combo in ((0, 1, 2), (3, 4, 5), (6, 7, 8)):
        y = size // 2
        draw.line([(0, y), (size, y)], fill=WIN_LINE_COLOR, width=6)
    elif winning_combo in ((0, 3, 6), (1, 4, 7), (2, 5, 8)):
        x = size // 2
        draw.line([(x, 0), (x, size)], fill=WIN_LINE_COLOR, width=6)
    elif winning_combo == (0, 4, 8):
        draw.line([(0, 0), (size, size)], fill=WIN_LINE_COLOR, width=6)
    elif winning_combo == (2, 4, 6):
        draw.line([(size, 0), (0, size)], fill=WIN_LINE_COLOR, width=6)


# same wood tile, with an X or O burned into it, optionally with a winning-line segment drawn on top
def make_marked_tile_image(mark, size=100, base_color=TILE_BASE_COLOR, winning_combo=None):
    texture = generate_wood_texture(size, size, base_color, TILE_GRAIN_COLOR)
    draw = ImageDraw.Draw(texture)
    padding = 22

    if mark == "X":
        draw.line([(padding, padding), (size - padding, size - padding)], fill=BOX_BORDER_COLOR, width=8)
        draw.line([(size - padding, padding), (padding, size - padding)], fill=BOX_BORDER_COLOR, width=8)
    else:
        draw.ellipse([padding, padding, size - padding, size - padding], outline=BOX_BORDER_COLOR, width=8)

    if winning_combo:
        draw_win_line_segment(draw, size, winning_combo)

    tile_image = ctk.CTkImage(light_image=texture, dark_image=texture, size=(size, size))
    tile_images.append(tile_image)
    return tile_image


# returns the winning combo of 3 indexes, or None if there isn't one yet
def check_winner():
    for combo in WIN_COMBOS:
        a, b, c = combo
        if board[a] is not None and board[a] == board[b] == board[c]:
            return combo
    return None


# locks the board, shows the result, highlights the winning line, and updates the score
def end_game(message, winning_combo, winner):
    global x_score, o_score, draw_score

    turn_label.configure(text=message)

    for button in cell_buttons:
        button.configure(state="disabled")

    if winning_combo:
        for index in winning_combo:
            image = make_marked_tile_image(board[index], base_color=WIN_TILE_COLOR, winning_combo=winning_combo)
            cell_buttons[index].configure(image=image)

    if winner == "X":
        x_score += 1
    elif winner == "O":
        o_score += 1
    else:
        draw_score += 1

    score_label.configure(text=f"X: {x_score}     O: {o_score}     Draws: {draw_score}")


# places the current player's mark on a clicked cell, checks for a win/draw, then hands the turn over
def place_mark(index, button):
    global current_player

    if board[index] is not None:
        return

    board[index] = current_player
    button.configure(image=make_marked_tile_image(current_player), state="disabled")

    winning_combo = check_winner()
    if winning_combo:
        end_game(f"{current_player} wins!", winning_combo, current_player)
        return

    if all(cell is not None for cell in board):
        end_game("It's a draw!", None, None)
        return

    current_player = "O" if current_player == "X" else "X"
    turn_label.configure(text=f"Turn: {current_player}")


# clears the board for a fresh round, without touching the score
def start_new_game():
    global board, current_player

    board = [None] * 9
    current_player = "X"
    turn_label.configure(text="Turn: X")

    for button in cell_buttons:
        button.configure(image=make_tile_image(), state="normal")


# the wooden box housing the whole game
box_frame = ctk.CTkFrame(app, corner_radius=20, fg_color=BOX_COLOR, border_width=2, border_color=BOX_BORDER_COLOR)
box_frame.pack(padx=20, pady=20)

title_label = ctk.CTkLabel(box_frame, text="TIC TAC TOE", font=("Georgia", 24, "bold"), text_color=CREAM)
title_label.pack(pady=(22, 4))

turn_label = ctk.CTkLabel(box_frame, text="Turn: X", font=("Georgia", 14, "bold"), text_color=CREAM)
turn_label.pack(pady=(0, 14))

# 3x3 grid of wood tile buttons
grid_frame = ctk.CTkFrame(box_frame, fg_color="transparent")
grid_frame.pack(padx=20)

for row in range(3):
    for col in range(3):
        index = row * 3 + col
        cell_button = ctk.CTkButton(
            grid_frame,
            text="",
            image=make_tile_image(),
            width=100,
            height=100,
            corner_radius=6,
            fg_color=BOX_COLOR,
            hover_color="#3a2110",
            border_width=0,
        )
        cell_button.configure(command=lambda index=index, button=cell_button: place_mark(index, button))
        cell_button.grid(row=row, column=col, padx=4, pady=4)
        cell_buttons.append(cell_button)

score_label = ctk.CTkLabel(box_frame, text="X: 0     O: 0     Draws: 0", font=("Georgia", 13, "bold"), text_color=CREAM)
score_label.pack(pady=(18, 10))

new_game_button = ctk.CTkButton(
    box_frame,
    text="New Game",
    height=36,
    corner_radius=14,
    font=("Georgia", 13, "bold"),
    fg_color=BOX_BORDER_COLOR,
    hover_color="#1c1109",
    text_color=CREAM,
    command=start_new_game,
)
new_game_button.pack(padx=20, pady=(0, 22), fill="x")


app.resizable(False, False)
app.mainloop()
