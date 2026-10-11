import json
import os
import requests
import customtkinter as ctk

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Currency Converter")
app.configure(fg_color="#f0f0f0")

CURRENCIES = requests.get("https://api.frankfurter.app/currencies").json()

RATE_CACHE_FILE = "rates_cache.json"


# load cached unit rates from the json file, or start with an empty dict if it's missing or empty
def load_rate_cache():
    if not os.path.exists(RATE_CACHE_FILE):
        return {}
    with open(RATE_CACHE_FILE, "r") as file:
        content = file.read().strip()
        return json.loads(content) if content else {}


# save the full rate cache back to the json file
def save_rate_cache(cache):
    with open(RATE_CACHE_FILE, "w") as file:
        json.dump(cache, file, indent=2)


rate_cache = load_rate_cache()


# converts the entered amount between the two selected currencies, using a cached rate if offline
def convert_currency():
    amount_text = amount_entry.get()
    try:
        amount = float(amount_text)
    except ValueError:
        result_label.configure(text="Enter a valid amount", text_color="#e74c3c")
        rate_label.configure(text="")
        return

    from_currency = from_button.cget("text")
    to_currency = to_button.cget("text")
    pair_key = f"{from_currency}_{to_currency}"

    offline = False
    try:
        response = requests.get(
            "https://api.frankfurter.app/latest",
            params={"amount": 1, "from": from_currency, "to": to_currency},
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
        unit_rate = data["rates"][to_currency]

        rate_cache[pair_key] = {"rate": unit_rate, "date": data["date"]}
        save_rate_cache(rate_cache)

    except (requests.exceptions.RequestException, KeyError):
        cached = rate_cache.get(pair_key)
        if not cached:
            result_label.configure(text="No internet and no cached rate for this pair", text_color="#e74c3c")
            rate_label.configure(text="")
            return
        unit_rate = cached["rate"]
        offline = True

    converted_amount = amount * unit_rate
    result_label.configure(text=f"{amount:.2f} {from_currency} = {converted_amount:.2f} {to_currency}", text_color="black")

    if offline:
        rate_label.configure(text=f"1 {from_currency} = {unit_rate:.4f} {to_currency}  (offline, cached {cached['date']})")
    else:
        rate_label.configure(text=f"1 {from_currency} = {unit_rate:.4f} {to_currency}")


# swaps the from and to currencies
def swap_currencies():
    from_currency = from_button.cget("text")
    to_currency = to_button.cget("text")

    from_button.configure(text=to_currency)
    to_button.configure(text=from_currency)


# opens a searchable popup listing every currency, and sets it on the target button when clicked
def open_currency_picker(target_button):
    popup = ctk.CTkToplevel(app)
    popup.title("Select Currency")
    popup.geometry("360x460")
    popup.configure(fg_color="#f0f0f0")
    popup.resizable(False, False)

    popup_card = ctk.CTkFrame(popup, corner_radius=20, fg_color="white", border_width=1, border_color="#e5e5e5")
    popup_card.pack(padx=20, pady=20, fill="both", expand=True)

    search_entry = ctk.CTkEntry(
        popup_card,
        height=40,
        corner_radius=12,
        font=("Arial", 14),
        fg_color="#f7f7f7",
        border_width=1,
        border_color="#e0e0e0",
        placeholder_text="Search currency...",
    )
    search_entry.pack(padx=20, pady=20, fill="x")

    list_frame = ctk.CTkScrollableFrame(popup_card, fg_color="transparent")
    list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    # picks a currency, updates the target button, and closes the popup
    def select_currency(code):
        target_button.configure(text=code)
        popup.destroy()

    # rebuilds the list of currency rows based on the current search text
    def render_list():
        for widget in list_frame.winfo_children():
            widget.destroy()

        query = search_entry.get().strip().lower()
        for code, name in CURRENCIES.items():
            if query and query not in code.lower() and query not in name.lower():
                continue

            row = ctk.CTkButton(
                list_frame,
                text=f"{code}  -  {name}",
                anchor="w",
                fg_color="transparent",
                text_color="black",
                hover_color="#f7f7f7",
                command=lambda code=code: select_currency(code),
            )
            row.pack(fill="x", pady=2)

    search_entry.bind("<KeyRelease>", lambda event: render_list())
    render_list()
    search_entry.focus()



card = ctk.CTkFrame(app, corner_radius=20, fg_color="white", border_width=1, border_color="#e5e5e5")
card.pack(padx=20, pady=20)

title_label = ctk.CTkLabel(card, text="Currency Converter", font=("Arial", 22, "bold"), text_color="black")
title_label.pack(pady=(22, 14))

amount_label = ctk.CTkLabel(card, text="AMOUNT", font=("Arial", 12, "bold"), text_color="#999999")
amount_label.pack(anchor="w", padx=20)

amount_entry = ctk.CTkEntry(
    card,
    width=340,
    height=42,
    corner_radius=12,
    font=("Arial", 14),
    fg_color="#f7f7f7",
    border_width=1,
    border_color="#e0e0e0",
    placeholder_text="e.g. 100",
)
amount_entry.pack(padx=20, pady=(5, 14))


currency_row = ctk.CTkFrame(card, fg_color="transparent")
currency_row.pack(padx=20, pady=(0, 14))

from_column = ctk.CTkFrame(currency_row, fg_color="transparent")
from_column.grid(row=0, column=0)

from_label = ctk.CTkLabel(from_column, text="FROM", font=("Arial", 12, "bold"), text_color="#999999")
from_label.pack(anchor="w")

from_button = ctk.CTkButton(
    from_column,
    text="USD",
    width=130,
    height=40,
    corner_radius=12,
    font=("Arial", 14, "bold"),
    fg_color="#f7f7f7",
    text_color="black",
    hover_color="#ececec",
    border_width=1,
    border_color="#e0e0e0",
)
from_button.configure(command=lambda: open_currency_picker(from_button))
from_button.pack(pady=(5, 0))

swap_button = ctk.CTkButton(
    currency_row,
    text="⇄",
    width=40,
    height=40,
    corner_radius=20,
    font=("Arial", 16, "bold"),
    fg_color="#e0e0e0",
    text_color="black",
    hover_color="#cfcfcf",
    command=swap_currencies,
)
swap_button.grid(row=0, column=1, padx=10, pady=(22, 0))

to_column = ctk.CTkFrame(currency_row, fg_color="transparent")
to_column.grid(row=0, column=2)

to_label = ctk.CTkLabel(to_column, text="TO", font=("Arial", 12, "bold"), text_color="#999999")
to_label.pack(anchor="w")

to_button = ctk.CTkButton(
    to_column,
    text="EUR",
    width=130,
    height=40,
    corner_radius=12,
    font=("Arial", 14, "bold"),
    fg_color="#f7f7f7",
    text_color="black",
    hover_color="#ececec",
    border_width=1,
    border_color="#e0e0e0",
)
to_button.configure(command=lambda: open_currency_picker(to_button))
to_button.pack(pady=(5, 0))


convert_button = ctk.CTkButton(
    card,
    text="Convert",
    height=42,
    corner_radius=18,
    font=("Arial", 15, "bold"),
    fg_color="#2f5fdc",
    hover_color="#2549b0",
    command=convert_currency,
)
convert_button.pack(padx=20, pady=(0, 14), fill="x")


result_frame = ctk.CTkFrame(card, width=340, height=64, corner_radius=12, fg_color="#f7f7f7", border_width=1, border_color="#e0e0e0")
result_frame.pack(padx=20, pady=(0, 6))
result_frame.pack_propagate(False)

result_label = ctk.CTkLabel(result_frame, text="Your result will appear here", text_color="#999999", font=("Arial", 16, "bold"))
result_label.pack(expand=True)

rate_label = ctk.CTkLabel(card, text="", font=("Arial", 12), text_color="#999999")
rate_label.pack(pady=(0, 20))


app.resizable(False, False)
app.mainloop()
