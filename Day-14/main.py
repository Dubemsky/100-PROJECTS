import json
import os
import customtkinter as ctk
import random

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Number Guessing Game")
app.configure(fg_color="#eef0f8")

ACCENT_COLOR = "#4f46e5"
ACCENT_HOVER = "#4338ca"
TINT_COLOR = "#f3f4fd"
TINT_BORDER = "#e3e6fb"

# max_guesses is one more than the perfect strategy needs
DIFFICULTIES = {
    "Easy": {"low": 1, "high": 50, "max_guesses": 7},
    "Medium": {"low": 1, "high": 100, "max_guesses": 8},
    "Hard": {"low": 1, "high": 1000, "max_guesses": 11},
}

SCORES_FILE = "best_scores.json"
TRICK_DELAY = 1100

TEMPERATURES = [
    ("Freezing", "#60a5fa"),
    ("Cold", "#22d3ee"),
    ("Warm", "#facc15"),
    ("Hot", "#fb923c"),
    ("Burning!", "#ef4444"),
]

BAR_WIDTH = 460

difficulty = "Medium"
secret_number = 0
range_low = 1
range_high = 100
guesses = []
guesses_left = 0
is_game_over = True
used_trick = False
trick_generation = 0


def load_scores():
    if not os.path.exists(SCORES_FILE):
        return {}
    with open(SCORES_FILE, "r") as file:
        content = file.read().strip()
        return json.loads(content) if content else {}


def save_scores(scores):
    with open(SCORES_FILE, "w") as file:
        json.dump(scores, file, indent=2)


# level 0 (freezing) to 4 (burning), indexes into TEMPERATURES
def get_temperature_level(guess):
    size = DIFFICULTIES[difficulty]["high"] - DIFFICULTIES[difficulty]["low"] + 1
    distance_ratio = abs(guess - secret_number) / size
    if distance_ratio <= 0.02:
        return 4
    if distance_ratio <= 0.05:
        return 3
    if distance_ratio <= 0.15:
        return 2
    if distance_ratio <= 0.3:
        return 1
    return 0


def get_closeness(guess):
    size = DIFFICULTIES[difficulty]["high"] - DIFFICULTIES[difficulty]["low"] + 1
    return max(0.06, 1 - abs(guess - secret_number) / (size * 0.5))


def get_trick_guess():
    return (range_low + range_high) // 2


def draw_temperature(fill_amount, level):
    temperature_canvas.delete("all")
    temperature_canvas.create_rectangle(0, 0, BAR_WIDTH, 26, fill=TINT_BORDER, outline="")
    if fill_amount > 0:
        temperature_canvas.create_rectangle(0, 0, BAR_WIDTH * fill_amount, 26, fill=TEMPERATURES[level][1], outline="")
    temperature_label.configure(
        text=TEMPERATURES[level][0] if fill_amount > 0 else "Make a guess to see how close you are",
        text_color=TEMPERATURES[level][1] if fill_amount > 0 else "#8a88a8",
    )


def draw_possible_numbers():
    start = DIFFICULTIES[difficulty]["low"]
    end = DIFFICULTIES[difficulty]["high"]
    total = end - start + 1
    possible_canvas.delete("all")
    possible_canvas.create_rectangle(0, 14, BAR_WIDTH, 40, fill=TINT_BORDER, outline="")
    left = BAR_WIDTH * (range_low - start) / total
    right = BAR_WIDTH * (range_high - start + 1) / total
    possible_canvas.create_rectangle(left, 14, right, 40, fill=ACCENT_COLOR, outline="")
    possible_canvas.create_text(2, 6, text=str(start), anchor="w", font=("Helvetica", 11, "bold"), fill="#8a88a8")
    possible_canvas.create_text(BAR_WIDTH - 2, 6, text=str(end), anchor="e", font=("Helvetica", 11, "bold"), fill="#8a88a8")
    possible_label.configure(text=f"{range_high - range_low + 1} numbers still possible")


def draw_history():
    for chip in history_frame.winfo_children():
        chip.destroy()
    for number, is_too_low in guesses:
        ctk.CTkLabel(
            history_frame, text=f"{number} {'↑' if is_too_low else '↓'}", font=("Helvetica", 14, "bold"),
            text_color="#1e1b3a", fg_color=TINT_COLOR, corner_radius=10, width=56, height=30,
        ).pack(side="left", padx=3)


def update_guesses_left():
    guesses_left_label.configure(text=str(guesses_left))


# returns "invalid", "won", "lost" or "continue"
def check_guess(guess):
    global range_low, range_high, guesses_left, is_game_over
    settings = DIFFICULTIES[difficulty]
    if guess < settings["low"] or guess > settings["high"]:
        message_label.configure(text=f"Pick a number between {settings['low']} and {settings['high']}", text_color="#dc2626")
        return "invalid"
    if guess in [number for number, _ in guesses]:
        message_label.configure(text="You already tried that one", text_color="#dc2626")
        return "invalid"

    guesses_left -= 1
    update_guesses_left()

    if guess == secret_number:
        range_low = range_high = guess
        guesses.append((guess, False))
        draw_history()
        draw_temperature(1, 4)
        draw_possible_numbers()
        end_game(True)
        return "won"

    is_too_low = guess < secret_number
    if is_too_low:
        range_low = max(range_low, guess + 1)
    else:
        range_high = min(range_high, guess - 1)
    guesses.append((guess, is_too_low))

    message_label.configure(text="Too low, go higher ↑" if is_too_low else "Too high, go lower ↓", text_color=ACCENT_COLOR)
    draw_temperature(get_closeness(guess), get_temperature_level(guess))
    draw_possible_numbers()
    draw_history()

    if guesses_left == 0:
        end_game(False)
        return "lost"
    return "continue"


def submit_guess(event=None):
    if is_game_over or used_trick:
        return
    text = guess_entry.get().strip()
    guess_entry.delete(0, "end")
    try:
        guess = int(text)
    except ValueError:
        message_label.configure(text="Type a whole number", text_color="#dc2626")
        return
    check_guess(guess)


def end_game(won):
    global is_game_over
    is_game_over = True
    guess_button.configure(state="disabled")
    guess_entry.configure(state="disabled")
    trick_button.configure(state="disabled")

    if won:
        used = len(guesses)
        result_title_label.configure(text="You got it!")
        result_detail_label.configure(text=f"The number was {secret_number}. You used {used} {'guess' if used == 1 else 'guesses'}.")
        scores = load_scores()
        if used_trick:
            result_note_label.configure(text="That's the trick: always guess the middle.")
        elif difficulty not in scores or used < scores[difficulty]:
            scores[difficulty] = used
            save_scores(scores)
            result_note_label.configure(text=f"New best for {difficulty}!")
        else:
            result_note_label.configure(text=f"Your best for {difficulty} is {scores[difficulty]}")
    else:
        result_title_label.configure(text="Out of guesses")
        result_detail_label.configure(text=f"The number was {secret_number}.")
        result_note_label.configure(text="Hint: guess the middle every time. Try Show me the trick!")
    result_frame.place(relx=0.5, rely=0.5, anchor="center")


def start_game(chosen_difficulty):
    global difficulty, secret_number, range_low, range_high, guesses, guesses_left, is_game_over, used_trick, trick_generation
    trick_generation += 1
    difficulty = chosen_difficulty
    settings = DIFFICULTIES[difficulty]
    secret_number = random.randint(settings["low"], settings["high"])
    range_low = settings["low"]
    range_high = settings["high"]
    guesses = []
    guesses_left = settings["max_guesses"]
    is_game_over = False
    used_trick = False

    result_frame.place_forget()
    difficulty_selector.set(difficulty)
    scores = load_scores()
    best_label.configure(text=f"Best: {scores[difficulty]}" if difficulty in scores else "No score yet")
    prompt_label.configure(text=f"Guess a number between {settings['low']} and {settings['high']}")
    message_label.configure(text="")
    update_guesses_left()
    guess_entry.configure(state="normal")
    guess_entry.delete(0, "end")
    guess_button.configure(state="normal")
    trick_button.configure(state="normal")
    draw_temperature(0, 0)
    draw_possible_numbers()
    draw_history()
    guess_entry.focus()


def start_trick():
    global used_trick
    if is_game_over or used_trick:
        return
    used_trick = True
    guess_button.configure(state="disabled")
    guess_entry.configure(state="disabled")
    trick_button.configure(state="disabled")
    message_label.configure(text="Always guess the middle...", text_color=ACCENT_COLOR)
    app.after(TRICK_DELAY, lambda: trick_step(trick_generation))


def trick_step(generation):
    if generation != trick_generation or is_game_over:
        return
    guess = get_trick_guess()
    guess_entry.configure(state="normal")
    guess_entry.delete(0, "end")
    guess_entry.insert(0, str(guess))
    guess_entry.configure(state="disabled")
    result = check_guess(guess)
    if result == "continue":
        app.after(TRICK_DELAY, lambda: trick_step(generation))


card = ctk.CTkFrame(app, corner_radius=22, fg_color="white", border_width=1, border_color=TINT_BORDER)
card.pack(padx=28, pady=20)

ctk.CTkLabel(card, text="Number Guessing", font=("Georgia", 22, "bold"), text_color="#1e1b3a").pack(pady=(20, 2))
ctk.CTkLabel(card, text="Pick a difficulty and start guessing", font=("Helvetica", 11), text_color="#8a88a8").pack(pady=(0, 14))

difficulty_selector = ctk.CTkSegmentedButton(
    card, values=list(DIFFICULTIES.keys()), command=start_game,
    width=340, height=32, corner_radius=12, font=("Helvetica", 12, "bold"),
    fg_color=TINT_COLOR, selected_color=ACCENT_COLOR, selected_hover_color=ACCENT_HOVER,
    unselected_color=TINT_COLOR, unselected_hover_color=TINT_BORDER, text_color="#1e1b3a",
)
difficulty_selector.pack(padx=28)

best_label = ctk.CTkLabel(card, text="", font=("Helvetica", 11, "bold"), text_color="#8a88a8")
best_label.pack(pady=(6, 12))

header_frame = ctk.CTkFrame(card, corner_radius=12, fg_color=ACCENT_COLOR)
header_frame.pack(padx=28, fill="x")

ctk.CTkLabel(header_frame, text="GUESSES LEFT", font=("Arial", 9, "bold"), text_color="#c9c4f7").pack(pady=(8, 0))
guesses_left_label = ctk.CTkLabel(header_frame, text="", font=("Georgia", 16, "bold"), text_color="white")
guesses_left_label.pack(pady=(0, 8))

prompt_label = ctk.CTkLabel(card, text="", font=("Georgia", 22, "bold"), text_color="#1e1b3a")
prompt_label.pack(padx=28, pady=(16, 12))

entry_row = ctk.CTkFrame(card, fg_color="transparent")
entry_row.pack()

guess_entry = ctk.CTkEntry(
    entry_row, width=170, height=50, font=("Helvetica", 24, "bold"), justify="center", corner_radius=12,
    fg_color="white", border_color=TINT_BORDER, border_width=2, text_color="#1e1b3a",
)
guess_entry.pack(side="left", padx=(0, 10))
guess_entry.bind("<Return>", submit_guess)

guess_button = ctk.CTkButton(
    entry_row, text="Guess", command=submit_guess, width=110, height=50, font=("Helvetica", 16, "bold"),
    corner_radius=12, fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER,
)
guess_button.pack(side="left")

message_label = ctk.CTkLabel(card, text="", font=("Helvetica", 18, "bold"), text_color=ACCENT_COLOR, height=34)
message_label.pack(pady=(10, 5))

stats_card = ctk.CTkFrame(card, corner_radius=14, fg_color=TINT_COLOR, border_width=1, border_color=TINT_BORDER)
stats_card.pack(padx=28, fill="x", pady=(4, 0))

ctk.CTkLabel(stats_card, text="TEMPERATURE", font=("Helvetica", 10, "bold"), text_color="#8a88a8").pack(anchor="w", padx=14, pady=(12, 0))
temperature_canvas = ctk.CTkCanvas(stats_card, width=BAR_WIDTH, height=22, highlightthickness=0, bg=TINT_COLOR)
temperature_canvas.pack(padx=14, pady=(5, 2))
temperature_label = ctk.CTkLabel(stats_card, text="", font=("Helvetica", 13, "bold"), text_color="#8a88a8")
temperature_label.pack(anchor="w", padx=14)

ctk.CTkLabel(stats_card, text="POSSIBLE NUMBERS", font=("Helvetica", 10, "bold"), text_color="#8a88a8").pack(anchor="w", padx=14, pady=(14, 0))
possible_canvas = ctk.CTkCanvas(stats_card, width=BAR_WIDTH, height=38, highlightthickness=0, bg=TINT_COLOR)
possible_canvas.pack(padx=14, pady=(5, 2))
possible_label = ctk.CTkLabel(stats_card, text="", font=("Helvetica", 12, "bold"), text_color=ACCENT_COLOR)
possible_label.pack(anchor="w", padx=14, pady=(0, 12))

history_frame = ctk.CTkFrame(card, fg_color="transparent", height=32)
history_frame.pack(padx=28, fill="x", pady=(12, 0))

button_row = ctk.CTkFrame(card, fg_color="transparent", height=36)
button_row.pack(padx=28, fill="x", pady=(14, 18))
button_row.pack_propagate(False)

trick_button = ctk.CTkButton(
    button_row, text="Show me the trick", command=start_trick, width=150, height=36, corner_radius=10,
    fg_color="transparent", text_color=ACCENT_COLOR, hover_color=TINT_COLOR, border_width=1.5, border_color=ACCENT_COLOR,
)
trick_button.pack()

# game over box, shown on top of the card
result_frame = ctk.CTkFrame(card, fg_color="white", corner_radius=18, border_width=1, border_color=TINT_BORDER)

result_title_label = ctk.CTkLabel(result_frame, text="", font=("Georgia", 26, "bold"), text_color="#1e1b3a")
result_title_label.pack(padx=46, pady=(22, 0))

result_detail_label = ctk.CTkLabel(result_frame, text="", font=("Helvetica", 15, "bold"), text_color=ACCENT_COLOR)
result_detail_label.pack(padx=28, pady=(4, 0))

result_note_label = ctk.CTkLabel(result_frame, text="", font=("Helvetica", 13), text_color="#8a88a8")
result_note_label.pack(padx=28, pady=(3, 14))

ctk.CTkButton(
    result_frame, text="Play Again", command=lambda: start_game(difficulty), width=170, height=40, corner_radius=10,
    font=("Helvetica", 14, "bold"), fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER,
).pack(pady=(0, 20))

app.update_idletasks()
start_game("Medium")
app.resizable(False, False)
app.mainloop()
