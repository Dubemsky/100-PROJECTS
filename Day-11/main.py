import json
import os
import random
import customtkinter as ctk

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Typing Speed Test")
app.configure(fg_color="#eef0f8")

ACCENT_COLOR = "#4f46e5"
ACCENT_HOVER = "#4338ca"
TINT_COLOR = "#f3f4fd"
TINT_BORDER = "#e3e6fb"

WORD_BANK = [
    "the", "quick", "brown", "fox", "jumps", "over", "lazy", "dog", "time", "speed",
    "keyboard", "practice", "makes", "perfect", "type", "fast", "slow", "word", "test",
    "random", "simple", "code", "python", "function", "button", "screen", "green", "red",
    "correct", "wrong", "letter", "space", "enter", "shift", "accuracy", "focus", "clear",
    "light", "dark", "color", "style", "design", "build", "create", "learn", "grow", "improve",
]

WORD_BUFFER_CHARS = 20

KEYBOARD_ROWS = [
    ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
    ["A", "S", "D", "F", "G", "H", "J", "K", "L", "'"],
    ["Shift", "Z", "X", "C", "V", "B", "N", "M", ",", "."],
]

KEY_PRESS_COLOR = "#c7c9e8"
TEST_DURATION = 30
SCORES_FILE = "scores.json"

KEY_BUTTONS = {}
typed_index = 0
current_text = ""
time_remaining = TEST_DURATION
timer_started = False
test_active = True


# load the best/last scores from the json file, or start fresh if it's missing or empty
def load_scores():
    defaults = {"best_wpm": 0, "best_accuracy": 0, "last_wpm": 0, "last_accuracy": 0}
    if not os.path.exists(SCORES_FILE):
        return defaults
    with open(SCORES_FILE, "r") as file:
        content = file.read().strip()
        return json.loads(content) if content else defaults


# save the best/last scores back to the json file
def save_scores():
    with open(SCORES_FILE, "w") as file:
        json.dump(scores, file, indent=2)


scores = load_scores()


# briefly grays out the on-screen key that matches what was physically typed
def flash_key(key):
    button = KEY_BUTTONS.get(key)
    if not button:
        return

    button.configure(fg_color=KEY_PRESS_COLOR)
    app.after(120, lambda: button.configure(fg_color=TINT_COLOR))

# re-colors a single character on the screen: pending, correct, or incorrect
def tag_char(index, tag):
    start = f"1.{index}"
    end = f"1.{index + 1}"
    screen.tag_remove("pending", start, end)
    screen.tag_remove("correct", start, end)
    screen.tag_remove("incorrect", start, end)
    screen.tag_add(tag, start, end)

# moves the highlighted "you are here" marker to the next character to be typed
def update_cursor():
    screen.tag_remove("current", "1.0", "end")
    if typed_index < len(current_text):
        screen.tag_add("current", f"1.{typed_index}", f"1.{typed_index + 1}")

# returns a string of random words from the word bank, joined by spaces
def generate_words(count):
    return " ".join(random.choice(WORD_BANK) for _ in range(count))

# appends another batch of random words to the end of the stream, tagged as pending
def append_words(count=10):
    global current_text

    addition = " " + generate_words(count)
    start_index = len(current_text)
    current_text += addition

    screen.configure(state="normal")
    screen.insert("end", addition)
    screen.configure(state="disabled")
    screen.tag_add("pending", f"1.{start_index}", f"1.{len(current_text)}")

# keeps the word stream topped up so the user never runs out of text to type
def ensure_enough_text():
    if len(current_text) - typed_index < WORD_BUFFER_CHARS:
        append_words()

# captures a physical keystroke, flashes the matching key, and judges it against the stream
def handle_keypress(event):
    global typed_index

    if not test_active:
        return

    if event.keysym == "BackSpace":
        if typed_index > 0:
            typed_index -= 1
            tag_char(typed_index, "pending")
            update_cursor()
            screen.see(f"1.{typed_index}")
        return

    key = event.char
    if not key or not key.isprintable():
        return

    if not timer_started:
        start_timer()

    flash_key(key.upper() if key.isalpha() else key)

    expected = current_text[typed_index]
    tag_char(typed_index, "correct" if key == expected else "incorrect")
    typed_index += 1
    ensure_enough_text()
    update_cursor()
    screen.see(f"1.{typed_index}")

# lights up the Shift key for as long as it's physically held down
def set_shift_highlight(is_down):
    shift_button.configure(fg_color=KEY_PRESS_COLOR if is_down else TINT_COLOR)

# starts the 30 second countdown, called on the very first keystroke
def start_timer():
    global timer_started
    timer_started = True
    app.after(1000, tick_timer)

# counts the clock down by one second, stopping the test once it hits 0
def tick_timer():
    global time_remaining, test_active

    if not timer_started:
        return

    time_remaining -= 1
    time_label.configure(text=str(time_remaining))

    if time_remaining <= 0:
        test_active = False
        calculate_results()
    else:
        app.after(1000, tick_timer)

# sums the length of every "correct"-tagged range on the screen
def count_correct_chars():
    ranges = screen.tag_ranges("correct")
    total = 0
    for i in range(0, len(ranges), 2):
        start_col = int(str(ranges[i]).split(".")[1])
        end_col = int(str(ranges[i + 1]).split(".")[1])
        total += end_col - start_col
    return total

# works out net WPM and accuracy from what's currently marked correct, and shows them
def calculate_results():
    correct_chars = count_correct_chars()
    minutes = TEST_DURATION / 60

    wpm = round((correct_chars / 5) / minutes)
    accuracy = round((correct_chars / typed_index) * 100) if typed_index > 0 else 100

    wpm_label.configure(text=str(wpm))
    accuracy_label.configure(text=f"{accuracy}%")

    scores["last_wpm"] = wpm
    scores["last_accuracy"] = accuracy
    if wpm > scores["best_wpm"]:
        scores["best_wpm"] = wpm
        scores["best_accuracy"] = accuracy
    save_scores()
    update_scores_label()

# shows the saved best and last WPM underneath the keyboard
def update_scores_label():
    scores_label.configure(text=f"BEST  {scores['best_wpm']} WPM        LAST  {scores['last_wpm']} WPM")

# resets the word stream, timer, and stats so another test can be taken
def reset_test():
    global typed_index, current_text, time_remaining, timer_started, test_active

    typed_index = 0
    time_remaining = TEST_DURATION
    timer_started = False
    test_active = True

    screen.configure(state="normal")
    screen.delete("1.0", "end")
    current_text = generate_words(20)
    screen.insert("1.0", current_text)
    screen.tag_add("pending", "1.0", "end")
    screen.configure(state="disabled")
    update_cursor()

    time_label.configure(text=str(TEST_DURATION))
    wpm_label.configure(text="0")
    accuracy_label.configure(text="100%")
    shift_button.configure(fg_color=TINT_COLOR)


# ---------- widgets: the app's layout ----------

# white card floating on the light tinted background
card = ctk.CTkFrame(app, corner_radius=22, fg_color="white", border_width=1, border_color="#e5e7f5")
card.pack(padx=18, pady=18)

title_label = ctk.CTkLabel(card, text="Typing Speed Test", font=("Georgia", 22, "bold"), text_color="#1e1b3a")
title_label.pack(pady=(22, 2))

subtitle_label = ctk.CTkLabel(card, text="Type as many words as you can before time runs out", font=("Arial", 11), text_color="#9796b8")
subtitle_label.pack(pady=(0, 16))

# stats pill: time / accuracy / wpm
stats_frame = ctk.CTkFrame(card, corner_radius=16, fg_color=ACCENT_COLOR)
stats_frame.pack(padx=20, pady=(0, 14), fill="x")

time_column = ctk.CTkFrame(stats_frame, fg_color="transparent")
time_column.pack(side="left", expand=True, fill="x", pady=4)
ctk.CTkLabel(time_column, text="TIME", font=("Arial", 9, "bold"), text_color="#c9c4f7").pack()
time_label = ctk.CTkLabel(time_column, text=str(TEST_DURATION), font=("Georgia", 18, "bold"), text_color="white")
time_label.pack()

divider1 = ctk.CTkFrame(stats_frame, width=1, height=1, fg_color="#7a71ea")
divider1.pack(side="left", fill="y", pady=4)

accuracy_column = ctk.CTkFrame(stats_frame, fg_color="transparent")
accuracy_column.pack(side="left", expand=True, fill="x", pady=4)
ctk.CTkLabel(accuracy_column, text="ACCURACY", font=("Arial", 9, "bold"), text_color="#c9c4f7").pack()
accuracy_label = ctk.CTkLabel(accuracy_column, text="100%", font=("Georgia", 18, "bold"), text_color="white")
accuracy_label.pack()

divider2 = ctk.CTkFrame(stats_frame, width=1, height=1, fg_color="#7a71ea")
divider2.pack(side="left", fill="y", pady=4)

wpm_column = ctk.CTkFrame(stats_frame, fg_color="transparent")
wpm_column.pack(side="left", expand=True, fill="x", pady=4)
ctk.CTkLabel(wpm_column, text="WPM", font=("Arial", 9, "bold"), text_color="#c9c4f7").pack()
wpm_label = ctk.CTkLabel(wpm_column, text="0", font=("Georgia", 18, "bold"), text_color="white")
wpm_label.pack()

# the screen: an endless word stream with live typing feedback
screen = ctk.CTkTextbox(
    card,
    width=460,
    height=160,
    corner_radius=14,
    fg_color=TINT_COLOR,
    border_width=1,
    border_color=TINT_BORDER,
    font=("Courier New", 18, "bold"),
    wrap="word",
)
screen.pack(padx=20, pady=(0, 16))
screen._textbox.configure(spacing1=5, spacing3=7)
screen.tag_config("pending", foreground="#4b4a63")
screen.tag_config("correct", foreground="#22c55e")
screen.tag_config("incorrect", foreground="#ef4444")
screen.tag_config("current", background="#c7c9e8")

current_text = generate_words(20)
screen.insert("1.0", current_text)
screen.tag_add("pending", "1.0", "end")
screen.configure(state="disabled")
update_cursor()

# on-screen keyboard
keyboard_frame = ctk.CTkFrame(card, fg_color="transparent")
keyboard_frame.pack(padx=20, pady=(0, 10))

for row_keys in KEYBOARD_ROWS:
    row_frame = ctk.CTkFrame(keyboard_frame, fg_color="transparent")
    row_frame.pack(pady=3)

    for key in row_keys:
        is_shift = key == "Shift"
        key_button = ctk.CTkButton(
            row_frame,
            text=key,
            width=54 if is_shift else 36,
            height=36,
            corner_radius=10,
            font=("Arial", 10 if is_shift else 12, "bold"),
            fg_color=TINT_COLOR,
            text_color="#1e1b3a",
            hover_color=TINT_BORDER,
            border_width=1,
            border_color=TINT_BORDER,
        )
        key_button.pack(side="left", padx=3)

        if is_shift:
            shift_button = key_button
        else:
            KEY_BUTTONS[key] = key_button

space_button = ctk.CTkButton(
    keyboard_frame,
    text="space",
    width=220,
    height=32,
    corner_radius=10,
    font=("Arial", 10, "bold"),
    fg_color=TINT_COLOR,
    text_color="#9796b8",
    hover_color=TINT_BORDER,
    border_width=1,
    border_color=TINT_BORDER,
)
space_button.pack(pady=(5, 0))
KEY_BUTTONS[" "] = space_button

scores_label = ctk.CTkLabel(card, text="", font=("Arial", 10, "bold"), text_color="#9796b8")
scores_label.pack(pady=(10, 0))

restart_button = ctk.CTkButton(
    card,
    text="New Test",
    height=38,
    corner_radius=14,
    font=("Arial", 14, "bold"),
    fg_color=ACCENT_COLOR,
    hover_color=ACCENT_HOVER,
    command=reset_test,
)
restart_button.pack(padx=20, pady=(14, 20), fill="x")


update_scores_label()

app.bind("<Key>", handle_keypress)
app.bind("<KeyPress-Shift_L>", lambda event: set_shift_highlight(True))
app.bind("<KeyRelease-Shift_L>", lambda event: set_shift_highlight(False))
app.bind("<KeyPress-Shift_R>", lambda event: set_shift_highlight(True))
app.bind("<KeyRelease-Shift_R>", lambda event: set_shift_highlight(False))
app.focus_set()

app.resizable(False, False)
app.mainloop()
