import random
import tkinter as tk
import customtkinter as ctk

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Hangman")
app.configure(fg_color="#f0f0f0")

WORD_CATEGORIES = {
    "Animals": ["ELEPHANT", "GIRAFFE", "PENGUIN", "DOLPHIN", "KANGAROO", "CROCODILE", "OCTOPUS", "CHEETAH"],
    "Countries": ["FRANCE", "BRAZIL", "JAPAN", "CANADA", "EGYPT", "GERMANY", "AUSTRALIA", "MEXICO"],
    "Movies": ["INCEPTION", "GLADIATOR", "TITANIC", "AVATAR", "FROZEN", "MATRIX", "JOKER", "JAWS"],
    "Tech": ["PYTHON", "HANGMAN", "KEYBOARD", "DESKTOP", "FUNCTION", "VARIABLE", "DEVELOPER", "COMPUTER"],
}
MAX_WRONG_GUESSES = 6
 
current_category = "Animals"
secret_word = random.choice(WORD_CATEGORIES[current_category])
guessed_letters = set()
wrong_guesses = 0
current_streak = 0
best_streak = 0

# builds the word display string, showing guessed letters and blanks for the rest
def get_display_word():
    return "  ".join(letter if letter in guessed_letters else "_" for letter in secret_word)


# disables every letter button, used once the round is won or lost
def disable_all_buttons():
    for row_frame in keyboard_frame.winfo_children():
        for button in row_frame.winfo_children():
            button.configure(state="disabled")


# ends the round: shows the message, updates the streak, and reveals the play again button
def end_round(message, color, won):
    global current_streak, best_streak

    if won:
        current_streak += 1
        best_streak = max(best_streak, current_streak)
    else:
        current_streak = 0

    streak_label.configure(text=f"Streak: {current_streak}   Best: {best_streak}")

    lives_label.configure(text=message, text_color=color)
    disable_all_buttons()
    play_again_button.pack(padx=20, pady=(0, 22))


# picks a new word and resets the board so a fresh round can start
def start_new_round():
    global secret_word, guessed_letters, wrong_guesses

    secret_word = random.choice(WORD_CATEGORIES[current_category])
    guessed_letters = set()
    wrong_guesses = 0

    draw_hangman(0)
    word_label.configure(text=get_display_word())
    lives_label.configure(text=f"{MAX_WRONG_GUESSES} lives left", text_color="#e74c3c")
    play_again_button.pack_forget()

    for row_frame in keyboard_frame.winfo_children():
        for button in row_frame.winfo_children():
            button.configure(state="normal", fg_color="#f7f7f7", border_color="#e0e0e0")


# switches the active category and starts a fresh round from it
def change_category(selected_category):
    global current_category
    current_category = selected_category
    start_new_round()


# handles a letter click: reveals it if correct, costs a life if wrong
def guess_letter(letter, button):
    global wrong_guesses

    guessed_letters.add(letter)
    button.configure(state="disabled")

    if letter in secret_word:
        button.configure(fg_color="#d7f5df", border_color="#2ecc71")
        word_label.configure(text=get_display_word())

        if all(char in guessed_letters for char in secret_word):
            end_round("You win!", "#2ecc71", won=True)
    else:
        wrong_guesses += 1
        button.configure(fg_color="#fbdcdc", border_color="#e74c3c")
        draw_hangman(wrong_guesses)
        lives_label.configure(text=f"{MAX_WRONG_GUESSES - wrong_guesses} lives left")

        if wrong_guesses >= MAX_WRONG_GUESSES:
            word_label.configure(text="  ".join(secret_word))
            end_round("You lose!", "#e74c3c", won=False)


# draws the gallows plus the hangman figure up to the given wrong-guess stage (0-6)
def draw_hangman(stage):
    hangman_canvas.delete("all")

    hangman_canvas.create_line(20, 170, 100, 170, width=3, fill="black")   
    hangman_canvas.create_line(40, 170, 40, 20, width=3, fill="black")    
    hangman_canvas.create_line(40, 20, 130, 20, width=3, fill="black")     
    hangman_canvas.create_line(130, 20, 130, 40, width=3, fill="black")    

    if stage >= 1:
        hangman_canvas.create_oval(110, 40, 150, 80, width=3, outline="black")  
    if stage >= 2:
        hangman_canvas.create_line(130, 80, 130, 130, width=3, fill="black")     
    if stage >= 3:
        hangman_canvas.create_line(130, 90, 105, 110, width=3, fill="black")      
    if stage >= 4:
        hangman_canvas.create_line(130, 90, 155, 110, width=3, fill="black")      
    if stage >= 5:
        hangman_canvas.create_line(130, 130, 110, 160, width=3, fill="black")   
    if stage >= 6:
        hangman_canvas.create_line(130, 130, 150, 160, width=3, fill="black")     


# white card floating on the light gray background
card = ctk.CTkFrame(app, corner_radius=20, fg_color="white", border_width=1, border_color="#e5e5e5")
card.pack(padx=20, pady=20)

title_label = ctk.CTkLabel(card, text="Hangman", font=("Arial", 22, "bold"), text_color="black")
title_label.pack(pady=(22, 2))

streak_label = ctk.CTkLabel(card, text="Streak: 0   Best: 0", font=("Arial", 11, "bold"), text_color="#999999")
streak_label.pack(pady=(0, 12))

# category picker
category_picker = ctk.CTkSegmentedButton(
    card,
    values=list(WORD_CATEGORIES.keys()),
    font=("Arial", 12, "bold"),
    corner_radius=12,
    height=38,
    fg_color="#f7f7f7",
    selected_color="#2f5fdc",
    selected_hover_color="#2549b0",
    unselected_color="#f7f7f7",
    unselected_hover_color="#ececec",
    text_color="black",
    text_color_disabled="black",
    command=change_category,
)
category_picker.set(current_category)
category_picker.pack(padx=20, pady=(0, 14))

# hangman drawing
canvas_frame = ctk.CTkFrame(card, width=220, height=200, corner_radius=12, fg_color="#f7f7f7", border_width=1, border_color="#e0e0e0")
canvas_frame.pack(padx=20, pady=(0, 14))
canvas_frame.pack_propagate(False)

hangman_canvas = tk.Canvas(canvas_frame, width=200, height=180, bg="#f7f7f7", highlightthickness=0)
hangman_canvas.pack(expand=True)

draw_hangman(0)

# word display
word_label = ctk.CTkLabel(card, text=get_display_word(), font=("Courier New", 26, "bold"), text_color="black")
word_label.pack(pady=(0, 10))

lives_label = ctk.CTkLabel(card, text=f"{MAX_WRONG_GUESSES} lives left", font=("Arial", 12, "bold"), text_color="#e74c3c")
lives_label.pack(pady=(0, 16))

# on-screen letter keyboard
keyboard_frame = ctk.CTkFrame(card, fg_color="transparent")
keyboard_frame.pack(padx=20, pady=(0, 22))

KEYBOARD_ROWS = [
    "QWERTYUIOP",
    "ASDFGHJKL",
    "ZXCVBNM",
]

for row_letters in KEYBOARD_ROWS:
    row_frame = ctk.CTkFrame(keyboard_frame, fg_color="transparent")
    row_frame.pack(pady=3)

    for letter in row_letters:
        letter_button = ctk.CTkButton(
            row_frame,
            text=letter,
            width=34,
            height=34,
            corner_radius=8,
            font=("Arial", 13, "bold"),
            fg_color="#f7f7f7",
            text_color="black",
            hover_color="#ececec",
            border_width=1,
            border_color="#e0e0e0",
        )
        letter_button.configure(command=lambda letter=letter, button=letter_button: guess_letter(letter, button))
        letter_button.pack(side="left", padx=2)

play_again_button = ctk.CTkButton(
    card,
    text="Play Again",
    height=36,
    corner_radius=16,
    font=("Arial", 13, "bold"),
    fg_color="#2f5fdc",
    hover_color="#2549b0",
    command=start_new_round,
)


app.resizable(False, False)
app.mainloop()
