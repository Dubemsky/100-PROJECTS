import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Calculator")

# display area
display_var = ctk.StringVar(value="")
display = ctk.CTkLabel(
    app,
    textvariable=display_var,
    font=("Arial", 32),
    anchor="e",
    width=330,
    height=80,
    corner_radius=10,
    fg_color="#1a1a2e",
    border_width=2,
    border_color="#4a4a6a",
)
display.grid(row=0, column=0, columnspan=3, padx=5, pady=10, sticky="nsew")


def set_display(text):
    display_var.set(text)
    if len(text) > 20:
        size = 16
    elif len(text) > 14:
        size = 22
    else:
        size = 32
    display.configure(font=("Arial", size))



history = ""
current_number = ""
first_number = None
operator = None


# handles what happens when a button is pressed
def on_button_click(text):
    global history, current_number, first_number, operator

    if text == "C":
        history = ""
        current_number = ""
        first_number = None
        operator = None
        set_display("")

    elif text == "+":
        current_number = current_number or "0"
        first_number = float(current_number)
        operator = "+"
        history = current_number + " + "
        current_number = ""
        set_display(history)

    elif text == "-":
        current_number = current_number or "0"
        first_number = float(current_number)
        operator = "-"
        history = current_number + " - "
        current_number = ""
        set_display(history)

    elif text == "*":
        current_number = current_number or "0"
        first_number = float(current_number)
        operator = "*"
        history = current_number + " * "
        current_number = ""
        set_display(history)

    elif text == "/":
        current_number = current_number or "0"
        first_number = float(current_number)
        operator = "/"
        history = current_number + " / "
        current_number = ""
        set_display(history)

    elif text == "=":
        if operator == "+":
            current_number = current_number or "0"
            second_number = float(current_number)
            result = first_number + second_number
            set_display(f"{history}{current_number} = {result}")
            history = ""
            current_number = ""
            first_number = None
            operator = None

        elif operator == "-":
            current_number = current_number or "0"
            second_number = float(current_number)
            result = first_number - second_number
            set_display(f"{history}{current_number} = {result}")
            history = ""
            current_number = ""
            first_number = None
            operator = None

        elif operator == "*":
            current_number = current_number or "0"
            second_number = float(current_number)
            result = first_number * second_number
            set_display(f"{history}{current_number} = {result}")
            history = ""
            current_number = ""
            first_number = None
            operator = None

        elif operator == "/":
            current_number = current_number or "0"
            second_number = float(current_number)
            if second_number == 0:
                set_display("Cannot divide by 0")
            else:
                result = first_number / second_number
                set_display(f"{history}{current_number} = {result}")
            history = ""
            current_number = ""
            first_number = None
            operator = None

    elif text == "⌫":
        current_number = current_number[:-1]
        set_display(history + current_number)

    elif text == "." and "." in current_number:
        pass

    else:
        current_number += text
        set_display(history + current_number)


# number buttons, laid out like a normal calculator
buttons = [
    ("7", 1, 0), ("8", 1, 1), ("9", 1, 2),
    ("4", 2, 0), ("5", 2, 1), ("6", 2, 2),
    ("1", 3, 0), ("2", 3, 1), ("3", 3, 2),
    (".", 4, 0), ("0", 4, 1), ("C", 4, 2),
]

# operator buttons, in their own column on the side
operator_buttons = [
    ("/", 1, 3),
    ("*", 2, 3),
    ("-", 3, 3),
    ("+", 4, 3),
]

for text, row, col in buttons:
    button = ctk.CTkButton(app, text=text, width=100, height=80, font=("Arial", 20), command=lambda t=text: on_button_click(t))
    button.grid(row=row, column=col, padx=5, pady=5)

for text, row, col in operator_buttons:
    button = ctk.CTkButton(app, text=text, width=80, height=80, font=("Arial", 20), fg_color="#4a4a6a", command=lambda t=text: on_button_click(t))
    button.grid(row=row, column=col, padx=5, pady=5)

equals_button = ctk.CTkButton(app, text="=", width=80, height=80, font=("Arial", 20), fg_color="#2f5fdc", command=lambda: on_button_click("="))
equals_button.grid(row=0, column=3, padx=5, pady=5)

backspace_button = ctk.CTkButton(app, text="⌫", height=60, font=("Arial", 20), fg_color="#4a4a6a", command=lambda: on_button_click("⌫"))
backspace_button.grid(row=5, column=0, columnspan=4, padx=5, pady=5, sticky="ew")

app.resizable(False, False)
app.mainloop()
