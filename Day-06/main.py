import json
import os
import secrets
import string
import customtkinter as ctk

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Password Generator")
app.configure(fg_color="#f0f0f0")

AMBIGUOUS_CHARACTERS = "0O1lI"
PASSWORDS_FILE = "passwords.json"

current_password = {"value": None}


# load saved passwords from the json file, or start with an empty list if it's missing or empty
def load_passwords():
    if not os.path.exists(PASSWORDS_FILE):
        return []
    with open(PASSWORDS_FILE, "r") as file:
        content = file.read().strip()
        return json.loads(content) if content else []


# save the full password list back to the json file
def save_passwords(passwords):
    with open(PASSWORDS_FILE, "w") as file:
        json.dump(passwords, file, indent=2)


saved_passwords = load_passwords()


# updates the length value label as the slider moves
def update_length_label(value):
    length_value_label.configure(text=str(int(value)))


# scores a password's strength and returns a label + color for it
def get_password_strength(password):
    score = 0

    length = len(password)
    if length >= 16:
        score += 3
    elif length >= 12:
        score += 2
    elif length >= 8:
        score += 1

    if any(char.isupper() for char in password):
        score += 1
    if any(char.islower() for char in password):
        score += 1
    if any(char.isdigit() for char in password):
        score += 1
    if any(char in string.punctuation for char in password):
        score += 1

    if score <= 3:
        return "Weak", "#e74c3c"
    if score <= 5:
        return "Medium", "#f1c40f"
    return "Strong", "#2ecc71"


# builds the pool of allowed characters from the checked character types
def get_character_pool():
    pool = ""
    if uppercase_checkbox.get():
        pool += string.ascii_uppercase
    if lowercase_checkbox.get():
        pool += string.ascii_lowercase
    if numbers_checkbox.get():
        pool += string.digits
    if symbols_checkbox.get():
        pool += string.punctuation

    if exclude_ambiguous_checkbox.get():
        pool = "".join(char for char in pool if char not in AMBIGUOUS_CHARACTERS)

    return pool


# builds a password from the checked character types and shows it
def generate_password():
    pool = get_character_pool()
    if not pool:
        password_label.configure(text="Select at least one character type", text_color="#e74c3c")
        strength_label.configure(text="")
        return

    length = int(length_slider.get())
    password = "".join(secrets.choice(pool) for _ in range(length))
    current_password["value"] = password

    password_label.configure(text=password, text_color="black")

    strength_text, strength_color = get_password_strength(password)
    strength_label.configure(text=f"Strength: {strength_text}", text_color=strength_color)


# saves the last generated password under the typed name
def save_password():
    name = name_entry.get().strip()
    password = current_password["value"]

    if not password:
        save_status_label.configure(text="Generate a password first", text_color="#e74c3c")
        return
    if not name:
        save_status_label.configure(text="Enter a name for this password", text_color="#e74c3c")
        return

    saved_passwords.append({"name": name, "password": password})
    save_passwords(saved_passwords)

    name_entry.delete(0, "end")
    save_status_label.configure(text=f"Saved as \"{name}\"", text_color="#2ecc71")


# copies one saved password to the clipboard, with a brief confirmation on its own button
def copy_saved_password(password, button):
    app.clipboard_clear()
    app.clipboard_append(password)

    button.configure(text="✓")
    app.after(1000, lambda: button.configure(text="Copy"))


# opens a popup listing every saved password
def open_view_passwords_popup():
    popup = ctk.CTkToplevel(app)
    popup.title("Saved Passwords")
    popup.geometry("360x420")
    popup.configure(fg_color="#f0f0f0")
    popup.resizable(False, False)

    popup_card = ctk.CTkFrame(popup, corner_radius=16, fg_color="white", border_width=1, border_color="#e5e5e5")
    popup_card.pack(padx=15, pady=15, fill="both", expand=True)

    title = ctk.CTkLabel(popup_card, text="Saved Passwords", font=("Arial", 18, "bold"), text_color="black")
    title.pack(pady=(20, 15))

    list_frame = ctk.CTkScrollableFrame(popup_card, fg_color="transparent")
    list_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    if not saved_passwords:
        ctk.CTkLabel(list_frame, text="No saved passwords yet", text_color="#999999").pack(pady=10)

    for entry in saved_passwords:
        row = ctk.CTkFrame(list_frame, fg_color="#f7f7f7", corner_radius=10)
        row.pack(fill="x", pady=4)

        text_column = ctk.CTkFrame(row, fg_color="transparent")
        text_column.pack(side="left", fill="x", expand=True, padx=(10, 5), pady=8)

        ctk.CTkLabel(text_column, text=entry["name"], font=("Arial", 13, "bold"), text_color="black", anchor="w").pack(fill="x")
        ctk.CTkLabel(text_column, text=entry["password"], font=("Arial", 11), text_color="#999999", anchor="w").pack(fill="x")

        copy_row_button = ctk.CTkButton(row, text="Copy", width=50, height=28, corner_radius=8, fg_color="#2f5fdc", hover_color="#2549b0")
        copy_row_button.configure(command=lambda p=entry["password"], b=copy_row_button: copy_saved_password(p, b))
        copy_row_button.pack(side="right", padx=10)


card = ctk.CTkFrame(app, corner_radius=16, fg_color="white", border_width=1, border_color="#e5e5e5")
card.pack(padx=15, pady=15)

title_label = ctk.CTkLabel(card, text="Password Generator", font=("Arial", 17, "bold"), text_color="black")
title_label.pack(pady=(15, 8))

password_display_frame = ctk.CTkFrame(card, width=300, height=40, corner_radius=10, fg_color="#f7f7f7", border_width=1, border_color="#e0e0e0")
password_display_frame.pack(padx=15)
password_display_frame.pack_propagate(False)

password_label = ctk.CTkLabel(password_display_frame, text="Your password will appear here", text_color="#999999", font=("Arial", 12))
password_label.pack(expand=True)

strength_label = ctk.CTkLabel(card, text="", font=("Arial", 10, "bold"))
strength_label.pack(pady=(3, 0))

length_row = ctk.CTkFrame(card, fg_color="transparent")
length_row.pack(fill="x", padx=15, pady=(8, 2))

length_title_label = ctk.CTkLabel(length_row, text="LENGTH", font=("Arial", 10, "bold"), text_color="#999999")
length_title_label.pack(side="left")

length_value_label = ctk.CTkLabel(length_row, text="16", font=("Arial", 10, "bold"), text_color="#2f5fdc")
length_value_label.pack(side="right")

length_slider = ctk.CTkSlider(card, from_=8, to=32, number_of_steps=24, command=update_length_label)
length_slider.set(16)
length_slider.pack(padx=15, pady=(0, 8), fill="x")

options_label = ctk.CTkLabel(card, text="CHARACTER TYPES", font=("Arial", 10, "bold"), text_color="#999999")
options_label.pack(anchor="w", padx=15)

options_frame = ctk.CTkFrame(card, fg_color="transparent")
options_frame.pack(fill="x", padx=15, pady=(3, 8))

uppercase_checkbox = ctk.CTkCheckBox(options_frame, text="Uppercase (A-Z)", text_color="black")
uppercase_checkbox.select()
uppercase_checkbox.pack(anchor="w", pady=2)

lowercase_checkbox = ctk.CTkCheckBox(options_frame, text="Lowercase (a-z)", text_color="black")
lowercase_checkbox.select()
lowercase_checkbox.pack(anchor="w", pady=2)

numbers_checkbox = ctk.CTkCheckBox(options_frame, text="Numbers (0-9)", text_color="black")
numbers_checkbox.select()
numbers_checkbox.pack(anchor="w", pady=2)

symbols_checkbox = ctk.CTkCheckBox(options_frame, text="Symbols (!@#$...)", text_color="black")
symbols_checkbox.select()
symbols_checkbox.pack(anchor="w", pady=2)

exclude_ambiguous_checkbox = ctk.CTkCheckBox(options_frame, text="Exclude ambiguous characters (0/O, 1/l/I)", text_color="black")
exclude_ambiguous_checkbox.pack(anchor="w", pady=2)

# generate button
generate_button = ctk.CTkButton(
    card,
    text="Generate",
    height=32,
    corner_radius=16,
    font=("Arial", 13, "bold"),
    fg_color="#2f5fdc",
    hover_color="#2549b0",
    command=generate_password,
)
generate_button.pack(padx=15, pady=(0, 8), fill="x")

save_label = ctk.CTkLabel(card, text="SAVE AS", font=("Arial", 10, "bold"), text_color="#999999")
save_label.pack(anchor="w", padx=15)

save_row = ctk.CTkFrame(card, fg_color="transparent")
save_row.pack(fill="x", padx=15, pady=(3, 3))

name_entry = ctk.CTkEntry(
    save_row,
    height=32,
    corner_radius=10,
    fg_color="#f7f7f7",
    border_width=1,
    border_color="#e0e0e0",
    placeholder_text="e.g. Facebook, Bank",
)
name_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

save_button = ctk.CTkButton(
    save_row,
    text="Save",
    width=60,
    height=32,
    corner_radius=10,
    fg_color="#2f5fdc",
    hover_color="#2549b0",
    command=save_password,
)
save_button.pack(side="left")

save_status_label = ctk.CTkLabel(card, text="", font=("Arial", 10, "bold"))
save_status_label.pack(pady=(0, 6))

view_button = ctk.CTkButton(
    card,
    text="View Saved Passwords",
    height=30,
    corner_radius=15,
    fg_color="#e0e0e0",
    text_color="black",
    hover_color="#cfcfcf",
    command=open_view_passwords_popup,
)
view_button.pack(padx=15, pady=(0, 15), fill="x")


app.resizable(False, False)
app.mainloop()
