import json
import os
import csv
import tkinter as tk
from tkinter import filedialog
from datetime import date, timedelta
import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg 

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Expense Tracker")
app.configure(fg_color="#f0f0f0")

CATEGORIES = ["Food", "Transport", "Bills", "Entertainment", "Shopping", "Other"]
ACCENT_COLOR = "#2f5fdc"
EXPENSES_FILE = "expenses.json"
BUDGETS_FILE = "budgets.json"

CHART_COLORS = ["#2f5fdc", "#5b8def", "#f2994a", "#eb5757", "#27ae60", "#9b51e0"]
CATEGORY_COLORS = dict(zip(CATEGORIES, CHART_COLORS))


# load saved expenses from the json file, or start with an empty list if it's missing or empty
def load_expenses():
    if not os.path.exists(EXPENSES_FILE):
        return []
    with open(EXPENSES_FILE, "r") as file:
        content = file.read().strip()
        return json.loads(content) if content else []


# save the full expenses list back to the json file
def save_expenses():
    with open(EXPENSES_FILE, "w") as file:
        json.dump(expenses, file, indent=2)


# load monthly budget limits per category from the json file
def load_budgets():
    if not os.path.exists(BUDGETS_FILE):
        return {}
    with open(BUDGETS_FILE, "r") as file:
        content = file.read().strip()
        return json.loads(content) if content else {}


# save the monthly budget limits back to the json file
def save_budgets():
    with open(BUDGETS_FILE, "w") as file:
        json.dump(budgets, file, indent=2)


expenses = load_expenses()
budgets = load_budgets()
current_filter = "All Time"


# builds one clickable, hoverable row for an expense
def create_expense_row(parent, expense):
    row = ctk.CTkFrame(parent, fg_color="white", corner_radius=8)
    row.pack(fill="x", pady=3, padx=2)

    info_column = ctk.CTkFrame(row, fg_color="transparent")
    info_column.pack(side="left", fill="x", expand=True, padx=(10, 5), pady=6)

    top_line = f"{expense['category']}   •   {expense['date']}"
    name_label = ctk.CTkLabel(info_column, text=top_line, font=("Arial", 11, "bold"), text_color="black", anchor="w")
    name_label.pack(fill="x")

    note_label = None
    if expense["note"]:
        note_label = ctk.CTkLabel(info_column, text=expense["note"], font=("Arial", 10), text_color="#999999", anchor="w")
        note_label.pack(fill="x")

    amount_label = ctk.CTkLabel(row, text=f"${expense['amount']:.2f}", font=("Arial", 12, "bold"), text_color=ACCENT_COLOR)
    amount_label.pack(side="right", padx=10)

    def on_enter(event):
        row.configure(fg_color="#eef1fa")

    def on_leave(event):
        row.configure(fg_color="white")

    widgets = [row, info_column, name_label, amount_label]
    if note_label:
        widgets.append(note_label)

    for widget in widgets:
        widget.bind("<Button-1>", lambda event, e=expense: open_edit_expense_form(e))
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)


# returns only the expenses that fall inside the currently selected date range
def get_filtered_expenses():
    if current_filter == "All Time":
        return expenses

    today = date.today()
    filtered = []
    for expense in expenses:
        expense_date = parse_expense_date(expense["date"])
        if not expense_date:
            continue

        if current_filter == "This Week":
            week_start = today - timedelta(days=today.weekday())
            in_range = week_start <= expense_date <= today
        elif current_filter == "This Month":
            in_range = expense_date.year == today.year and expense_date.month == today.month
        else:
            in_range = expense_date.year == today.year

        if in_range:
            filtered.append(expense)

    return filtered


# rebuilds the history list from the filtered expenses, newest first
def render_history():
    for widget in history_frame.winfo_children():
        widget.destroy()

    if not expenses:
        ctk.CTkLabel(history_frame, text="No expenses yet", text_color="#999999").pack(pady=8)
        return

    filtered = get_filtered_expenses()
    if not filtered:
        ctk.CTkLabel(history_frame, text="No expenses in this range", text_color="#999999").pack(pady=8)
        return

    for expense in reversed(filtered):
        create_expense_row(history_frame, expense)


# changes the date range filter and redraws the history and chart
def set_filter(selected_filter):
    global current_filter
    current_filter = selected_filter
    render_history()
    render_chart()


# popup for editing or deleting an existing expense
def open_edit_expense_form(expense):
    form = ctk.CTkToplevel(app)
    form.title("Edit Expense")
    form.geometry("300x560")
    form.configure(fg_color="#f0f0f0")
    form.resizable(False, False)

    card = ctk.CTkFrame(form, corner_radius=16, fg_color="white", border_width=1, border_color="#e5e5e5")
    card.pack(padx=20, pady=20, fill="both", expand=True)

    title = ctk.CTkLabel(card, text="Edit Expense", font=("Arial", 18, "bold"), text_color="black")
    title.pack(pady=(20, 16))

    ctk.CTkLabel(card, text="AMOUNT", font=("Arial", 10, "bold"), text_color="#999999").pack(anchor="w", padx=20)
    amount_entry = ctk.CTkEntry(card, height=36, corner_radius=10, fg_color="#f7f7f7", border_width=1, border_color="#e0e0e0")
    amount_entry.insert(0, f"{expense['amount']:.2f}")
    amount_entry.pack(padx=20, pady=(4, 12), fill="x")

    ctk.CTkLabel(card, text="CATEGORY", font=("Arial", 10, "bold"), text_color="#999999").pack(anchor="w", padx=20)
    edit_category_menu = ctk.CTkOptionMenu(
        card,
        values=CATEGORIES,
        height=36,
        corner_radius=10,
        fg_color="#f7f7f7",
        button_color="#e0e0e0",
        button_hover_color="#cfcfcf",
        text_color="black",
        dropdown_fg_color="white",
        dropdown_text_color="black",
    )
    edit_category_menu.set(expense["category"])
    edit_category_menu.pack(padx=20, pady=(4, 12), fill="x")

    ctk.CTkLabel(card, text="DATE", font=("Arial", 10, "bold"), text_color="#999999").pack(anchor="w", padx=20)
    edit_date_entry = ctk.CTkEntry(card, height=36, corner_radius=10, fg_color="#f7f7f7", border_width=1, border_color="#e0e0e0")
    edit_date_entry.insert(0, expense["date"])
    edit_date_entry.pack(padx=20, pady=(4, 12), fill="x")

    ctk.CTkLabel(card, text="NOTE", font=("Arial", 10, "bold"), text_color="#999999").pack(anchor="w", padx=20)
    edit_note_entry = ctk.CTkEntry(card, height=36, corner_radius=10, fg_color="#f7f7f7", border_width=1, border_color="#e0e0e0")
    edit_note_entry.insert(0, expense["note"])
    edit_note_entry.pack(padx=20, pady=(4, 16), fill="x")

    update_button = ctk.CTkButton(
        card,
        text="Update",
        height=38,
        corner_radius=10,
        font=("Arial", 13, "bold"),
        fg_color=ACCENT_COLOR,
        hover_color="#2549b0",
        command=lambda: update_expense(form, expense, amount_entry, edit_category_menu, edit_date_entry, edit_note_entry),
    )
    update_button.pack(padx=20, pady=(0, 10), fill="x")

    delete_button = ctk.CTkButton(
        card,
        text="Delete",
        height=38,
        corner_radius=10,
        font=("Arial", 13, "bold"),
        fg_color="#e74c3c",
        hover_color="#c0392b",
        command=lambda: delete_expense(form, expense),
    )
    delete_button.pack(padx=20, pady=(0, 20), fill="x")


# updates an expense with new values and closes the edit popup
def update_expense(form, expense, amount_entry, category_menu, date_entry, note_entry):
    amount_text = amount_entry.get().strip()
    try:
        amount = float(amount_text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        amount_entry.configure(border_color="#e74c3c")
        return

    expense["amount"] = amount
    expense["category"] = category_menu.get()
    expense["date"] = date_entry.get().strip()
    expense["note"] = note_entry.get().strip()
    save_expenses()

    form.destroy()
    render_history()
    update_total()
    render_chart()
    render_budgets()


# deletes an expense and closes the edit popup
def delete_expense(form, expense):
    expenses.remove(expense)
    save_expenses()

    form.destroy()
    render_history()
    update_total()
    render_chart()
    render_budgets()


# parses an expense's date string, or None if it isn't a valid date
def parse_expense_date(date_text):
    try:
        return date.fromisoformat(date_text)
    except ValueError:
        return None


# recalculates and displays this month's total and the all-time total
def update_total():
    total = sum(expense["amount"] for expense in expenses)
    total_label.configure(text=f"${total:.2f}")

    today = date.today()
    month_total = 0
    for expense in expenses:
        expense_date = parse_expense_date(expense["date"])
        if expense_date and expense_date.year == today.year and expense_date.month == today.month:
            month_total += expense["amount"]

    month_total_label.configure(text=f"${month_total:.2f}")


# redraws the category breakdown pie chart from the expenses list
def render_chart():
    for widget in chart_frame.winfo_children():
        widget.destroy()

    category_totals = {}
    for expense in get_filtered_expenses():
        category_totals[expense["category"]] = category_totals.get(expense["category"], 0) + expense["amount"]

    if not category_totals:
        ctk.CTkLabel(chart_frame, text="No data yet", text_color="#999999").pack(pady=40)
        return

    labels = list(category_totals.keys())
    sizes = list(category_totals.values())
    colors = [CATEGORY_COLORS.get(label, "#999999") for label in labels]

    figure = Figure(figsize=(3.4, 2.3), dpi=100)
    figure.patch.set_facecolor("#f7f7f7")

    axes = figure.add_subplot(111)
    axes.pie(sizes, labels=labels, autopct="%1.0f%%", colors=colors, textprops={"fontsize": 8})

    canvas = FigureCanvasTkAgg(figure, master=chart_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(pady=4)


# totals this month's spending for each category
def get_month_spent_by_category():
    today = date.today()
    spent = {}
    for expense in expenses:
        expense_date = parse_expense_date(expense["date"])
        if expense_date and expense_date.year == today.year and expense_date.month == today.month:
            spent[expense["category"]] = spent.get(expense["category"], 0) + expense["amount"]
    return spent


# builds one budget row showing spending against the category's monthly limit
def create_budget_row(parent, category, spent):
    limit = budgets.get(category)
    over_budget = limit is not None and spent > limit

    row = ctk.CTkFrame(parent, fg_color="white", corner_radius=8)
    row.pack(fill="x", pady=3, padx=2)

    top = ctk.CTkFrame(row, fg_color="transparent")
    top.pack(fill="x", padx=10, pady=(6, 2))

    category_label = ctk.CTkLabel(top, text=category, font=("Arial", 11, "bold"), text_color="black")
    category_label.pack(side="left")

    if limit is None:
        status_text, status_color = "No budget set", "#999999"
    else:
        status_text = f"${spent:.2f} / ${limit:.2f}"
        status_color = "#e74c3c" if over_budget else "#999999"
    status_label = ctk.CTkLabel(top, text=status_text, font=("Arial", 10, "bold"), text_color=status_color)
    status_label.pack(side="right")

    track = tk.Frame(row, height=8, bg="#e8e8e8")
    track.pack(fill="x", padx=10, pady=(0, 8))
    track.pack_propagate(False)

    fill = tk.Frame(track, bg="#e74c3c" if over_budget else ACCENT_COLOR)
    fill.place(relx=0, rely=0, relwidth=min(spent / limit, 1) if limit else 0, relheight=1)

    for widget in [row, top, category_label, status_label, track, fill]:
        widget.bind("<Button-1>", lambda event, c=category: open_budget_form(c))


# redraws every category's budget row for this month
def render_budgets():
    for widget in budgets_frame.winfo_children():
        widget.destroy()

    spent = get_month_spent_by_category()
    for category in CATEGORIES:
        create_budget_row(budgets_frame, category, spent.get(category, 0))


# popup for setting a category's monthly budget limit
def open_budget_form(category):
    form = ctk.CTkToplevel(app)
    form.title("Set Budget")
    form.geometry("300x260")
    form.configure(fg_color="#f0f0f0")
    form.resizable(False, False)

    card = ctk.CTkFrame(form, corner_radius=16, fg_color="white", border_width=1, border_color="#e5e5e5")
    card.pack(padx=20, pady=20, fill="both", expand=True)

    ctk.CTkLabel(card, text=f"{category} budget", font=("Arial", 16, "bold"), text_color="black").pack(pady=(20, 12))

    ctk.CTkLabel(card, text="MONTHLY LIMIT", font=("Arial", 10, "bold"), text_color="#999999").pack(anchor="w", padx=20)
    limit_entry = ctk.CTkEntry(
        card,
        height=36,
        corner_radius=10,
        fg_color="#f7f7f7",
        border_width=1,
        border_color="#e0e0e0",
        placeholder_text="e.g. 200",
    )
    if budgets.get(category):
        limit_entry.insert(0, f"{budgets[category]:.2f}")
    limit_entry.pack(padx=20, pady=(4, 16), fill="x")

    save_button = ctk.CTkButton(
        card,
        text="Save",
        height=38,
        corner_radius=10,
        font=("Arial", 13, "bold"),
        fg_color=ACCENT_COLOR,
        hover_color="#2549b0",
        command=lambda: save_budget(form, category, limit_entry),
    )
    save_button.pack(padx=20, fill="x")


# saves a category's budget limit and closes the popup
def save_budget(form, category, limit_entry):
    try:
        limit = float(limit_entry.get().strip())
        if limit <= 0:
            raise ValueError
    except ValueError:
        limit_entry.configure(border_color="#e74c3c")
        return

    budgets[category] = limit
    save_budgets()

    form.destroy()
    render_budgets()


# saves every expense to a CSV file the user picks
def export_csv():
    path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        initialfile="expenses.csv",
        filetypes=[("CSV files", "*.csv")],
    )
    if not path:
        return

    with open(path, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["date", "category", "amount", "note"])
        writer.writeheader()
        for expense in expenses:
            writer.writerow({
                "date": expense["date"],
                "category": expense["category"],
                "amount": f"{expense['amount']:.2f}",
                "note": expense["note"],
            })

    export_button.configure(text="Exported")
    app.after(1500, lambda: export_button.configure(text="Export CSV"))


# reads the form, validates the amount, and adds a new expense
def add_expense():
    amount_text = amount_entry.get().strip()
    try:
        amount = float(amount_text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        amount_entry.configure(border_color="#e74c3c")
        return

    amount_entry.configure(border_color="#e0e0e0")

    expenses.append({
        "amount": amount,
        "category": category_menu.get(),
        "date": date_entry.get().strip(),
        "note": note_entry.get().strip(),
    })
    save_expenses()

    amount_entry.delete(0, "end")
    note_entry.delete(0, "end")

    render_history()
    update_total()
    render_chart()
    render_budgets()


card = ctk.CTkFrame(app, corner_radius=16, fg_color="white", border_width=1, border_color="#e5e5e5")
card.pack(padx=12, pady=12)

title_label = ctk.CTkLabel(card, text="Expense Tracker", font=("Arial", 16, "bold"), text_color="black")
title_label.pack(pady=(14, 1))

subtitle_label = ctk.CTkLabel(card, text="Track your spending, one expense at a time", font=("Arial", 10), text_color="#999999")
subtitle_label.pack(pady=(0, 10))

# total spent stat pill, split into this month / all time
total_frame = ctk.CTkFrame(card, corner_radius=12, fg_color=ACCENT_COLOR)
total_frame.pack(padx=14, pady=(0, 8), fill="x")

month_column = ctk.CTkFrame(total_frame, fg_color="transparent")
month_column.pack(side="left", expand=True, fill="x", pady=6)

ctk.CTkLabel(month_column, text="THIS MONTH", font=("Arial", 8, "bold"), text_color="#c9d7f7").pack()
month_total_label = ctk.CTkLabel(month_column, text="$0.00", font=("Arial", 15, "bold"), text_color="white")
month_total_label.pack(pady=(1, 0))

divider = ctk.CTkFrame(total_frame, width=1, height=1, fg_color="#6c87e0")
divider.pack(side="left", fill="y", pady=8)

alltime_column = ctk.CTkFrame(total_frame, fg_color="transparent")
alltime_column.pack(side="left", expand=True, fill="x", pady=6)

ctk.CTkLabel(alltime_column, text="ALL TIME", font=("Arial", 8, "bold"), text_color="#c9d7f7").pack()
total_label = ctk.CTkLabel(alltime_column, text="$0.00", font=("Arial", 15, "bold"), text_color="white")
total_label.pack(pady=(1, 0))

# add expense section
form_section = ctk.CTkFrame(card, corner_radius=12, fg_color="#f7f7f7")
form_section.pack(padx=14, pady=(0, 6), fill="x")

form_header = ctk.CTkLabel(form_section, text="ADD EXPENSE", font=("Arial", 9, "bold"), text_color="#999999")
form_header.pack(anchor="w", padx=12, pady=(10, 6))

row1 = ctk.CTkFrame(form_section, fg_color="transparent")
row1.pack(fill="x", padx=12)

amount_column = ctk.CTkFrame(row1, fg_color="transparent")
amount_column.pack(side="left", padx=(0, 6))
ctk.CTkLabel(amount_column, text="AMOUNT", font=("Arial", 8, "bold"), text_color="#aaaaaa").pack(anchor="w")
amount_entry = ctk.CTkEntry(
    amount_column,
    width=80,
    height=28,
    corner_radius=8,
    fg_color="white",
    border_width=1,
    border_color="#e0e0e0",
    placeholder_text="0.00",
)
amount_entry.pack(pady=(2, 0))

category_column = ctk.CTkFrame(row1, fg_color="transparent")
category_column.pack(side="left", padx=(0, 6))
ctk.CTkLabel(category_column, text="CATEGORY", font=("Arial", 8, "bold"), text_color="#aaaaaa").pack(anchor="w")
category_menu = ctk.CTkOptionMenu(
    category_column,
    values=CATEGORIES,
    width=112,
    height=28,
    corner_radius=8,
    fg_color="white",
    button_color="#e0e0e0",
    button_hover_color="#cfcfcf",
    text_color="black",
    dropdown_fg_color="white",
    dropdown_text_color="black",
)
category_menu.pack(pady=(2, 0))

date_column = ctk.CTkFrame(row1, fg_color="transparent")
date_column.pack(side="left")
ctk.CTkLabel(date_column, text="DATE", font=("Arial", 8, "bold"), text_color="#aaaaaa").pack(anchor="w")
date_entry = ctk.CTkEntry(
    date_column,
    width=94,
    height=28,
    corner_radius=8,
    fg_color="white",
    border_width=1,
    border_color="#e0e0e0",
)
date_entry.insert(0, date.today().isoformat())
date_entry.pack(pady=(2, 0))

note_column = ctk.CTkFrame(form_section, fg_color="transparent")
note_column.pack(fill="x", padx=12, pady=(6, 0))
ctk.CTkLabel(note_column, text="NOTE (OPTIONAL)", font=("Arial", 8, "bold"), text_color="#aaaaaa").pack(anchor="w")
note_entry = ctk.CTkEntry(
    note_column,
    height=28,
    corner_radius=8,
    fg_color="white",
    border_width=1,
    border_color="#e0e0e0",
    placeholder_text="e.g. Weekly grocery run",
)
note_entry.pack(pady=(2, 0), fill="x")

add_button = ctk.CTkButton(
    form_section,
    text="Add Expense",
    height=30,
    corner_radius=10,
    font=("Arial", 12, "bold"),
    fg_color=ACCENT_COLOR,
    hover_color="#2549b0",
    command=add_expense,
)
add_button.pack(padx=12, pady=(10, 12), fill="x")

history_breakdown_tabs = ctk.CTkTabview(
    card,
    width=340,
    height=250,
    corner_radius=10,
    fg_color="#f7f7f7",
    segmented_button_fg_color="#f7f7f7",
    segmented_button_font=("Arial", 12, "bold"),
    segmented_button_selected_color=ACCENT_COLOR,
    segmented_button_selected_hover_color="#2549b0",
    segmented_button_unselected_color="#8aa6ea",
    segmented_button_unselected_hover_color="#7593e0",
    text_color="white",
    text_color_disabled="white",
)
filter_header = ctk.CTkFrame(card, fg_color="transparent")
filter_header.pack(fill="x", padx=14, pady=(4, 3))

filter_label = ctk.CTkLabel(filter_header, text="SHOW EXPENSES FROM", font=("Arial", 9, "bold"), text_color="#2f5fdc")
filter_label.pack(side="left")

export_button = ctk.CTkButton(
    filter_header,
    text="Export CSV",
    width=90,
    height=22,
    corner_radius=8,
    font=("Arial", 10, "bold"),
    fg_color="#e8eefc",
    text_color=ACCENT_COLOR,
    hover_color="#d4def7",
    command=export_csv,
)
export_button.pack(side="right")

filter_control = ctk.CTkSegmentedButton(
    card,
    values=["This Week", "This Month", "This Year", "All Time"],
    width=340,
    height=30,
    corner_radius=15,
    font=("Arial", 10, "bold"),
    fg_color="#f7f7f7",
    selected_color=ACCENT_COLOR,
    selected_hover_color="#2549b0",
    unselected_color="#8aa6ea",
    unselected_hover_color="#7593e0",
    text_color="white",
    text_color_disabled="white",
    command=set_filter,
)
filter_control.set(current_filter)
filter_control.pack(padx=14, pady=(0, 8))

history_breakdown_tabs._segmented_button.configure(height=34)
history_breakdown_tabs.pack(padx=14, pady=(0, 14))
history_breakdown_tabs.add("History")
history_breakdown_tabs.add("Breakdown")
history_breakdown_tabs.add("Budgets")

history_frame = ctk.CTkScrollableFrame(history_breakdown_tabs.tab("History"), fg_color="transparent")
history_frame.pack(fill="both", expand=True)

chart_frame = ctk.CTkFrame(history_breakdown_tabs.tab("Breakdown"), fg_color="transparent")
chart_frame.pack(fill="both", expand=True)

budgets_frame = ctk.CTkScrollableFrame(history_breakdown_tabs.tab("Budgets"), fg_color="transparent")
budgets_frame.pack(fill="both", expand=True)

render_history()
update_total()
render_chart()
render_budgets()


app.resizable(False, False)
app.mainloop()
