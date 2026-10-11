import json
import os
import calendar
from datetime import date
import customtkinter as ctk

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


app = ctk.CTk()
app.title("Day 4")
app.configure(fg_color="white")
app.geometry("500x600")

TASKS_FILE = "tasks.json"


# ---------- data: load and save tasks from the json file ----------

def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return []
    with open(TASKS_FILE, "r") as file:
        content = file.read().strip()
        return json.loads(content) if content else []


def save_tasks(tasks):
    with open(TASKS_FILE, "w") as file:
        json.dump(tasks, file, indent=2)


tasks = load_tasks()



# saves a new task and closes the add task popup
def save_new_task(form, name_entry, date_display):
    task_name = name_entry.get()
    due_date = date_display.cget("text")

    tasks.append({"task_name": task_name, "due_date": due_date, "completed": False})
    save_tasks(tasks)

    form.destroy()
    render_tasks()


# updates a task with new values and closes the edit popup
def update_task(form, task, name_entry, date_display):
    task["task_name"] = name_entry.get()
    task["due_date"] = date_display.cget("text")
    save_tasks(tasks)

    form.destroy()
    render_tasks()


# toggles a task between complete and incomplete
def toggle_complete(form, task):
    task["completed"] = not task.get("completed", False)
    save_tasks(tasks)

    form.destroy()
    render_tasks()


# deletes a task
def delete_task(form, task):
    tasks.remove(task)
    save_tasks(tasks)

    form.destroy()
    render_tasks()



# popup for editing an existing task's name and due date
def open_edit_task_form(task):
    form = ctk.CTkToplevel(app)
    form.title("Edit Task")
    form.geometry("320x530")
    form.configure(fg_color="#f0f0f0")
    form.resizable(False, False)

    card = ctk.CTkFrame(form, corner_radius=16, fg_color="white", border_width=1, border_color="#e5e5e5")
    card.pack(padx=20, pady=20, fill="both", expand=True)

    title = ctk.CTkLabel(card, text="Edit Task", font=("Arial", 19, "bold"), text_color="black")
    title.pack(pady=(25, 20))

    name_label = ctk.CTkLabel(card, text="TASK NAME", font=("Arial", 11, "bold"), text_color="#999999")
    name_label.pack(anchor="w", padx=25)
    name_entry = ctk.CTkEntry(
        card,
        width=250,
        height=38,
        corner_radius=10,
        fg_color="#f7f7f7",
        border_width=1,
        border_color="#e0e0e0",
    )
    name_entry.insert(0, task["task_name"])
    name_entry.pack(pady=(6, 20), padx=25)

    date_label = ctk.CTkLabel(card, text="DUE DATE", font=("Arial", 11, "bold"), text_color="#999999")
    date_label.pack(anchor="w", padx=25)

    date_row = ctk.CTkFrame(card, fg_color="#f7f7f7", corner_radius=10, border_width=1, border_color="#e0e0e0", height=38)
    date_row.pack(fill="x", padx=25, pady=(6, 25))
    date_row.pack_propagate(False)

    date_display = ctk.CTkLabel(date_row, text=task["due_date"], text_color="black", font=("Arial", 13))
    date_display.pack(side="left", padx=(12, 0))

    date_button = ctk.CTkButton(
        date_row,
        text="📅",
        width=32,
        height=28,
        corner_radius=8,
        fg_color="#e8ecf7",
        text_color="black",
        hover_color="#d6ddf0",
        command=lambda: open_calendar_popup(form, date_display),
    )
    date_button.pack(side="right", padx=5)

    update_button = ctk.CTkButton(
        card,
        text="Update",
        height=42,
        corner_radius=10,
        font=("Arial", 14, "bold"),
        fg_color="#2f5fdc",
        hover_color="#2549b0",
        command=lambda: update_task(form, task, name_entry, date_display),
    )
    update_button.pack(pady=(0, 10), padx=25, fill="x")

    is_completed = task.get("completed", False)
    complete_button = ctk.CTkButton(
        card,
        text="Mark as Incomplete" if is_completed else "Mark as Complete",
        height=42,
        corner_radius=10,
        font=("Arial", 14, "bold"),
        fg_color="#e0e0e0" if is_completed else "#2ecc71",
        text_color="black" if is_completed else "white",
        hover_color="#cfcfcf" if is_completed else "#27ae60",
        command=lambda: toggle_complete(form, task),
    )
    complete_button.pack(pady=(0, 10), padx=25, fill="x")

    delete_button = ctk.CTkButton(
        card,
        text="🗑 Delete",
        height=42,
        corner_radius=10,
        font=("Arial", 14, "bold"),
        fg_color="#e74c3c",
        hover_color="#c0392b",
        command=lambda: delete_task(form, task),
    )
    delete_button.pack(pady=(0, 25), padx=25, fill="x")


# popup calendar (built from the standard "calendar" module) for picking a date
def open_calendar_popup(form, date_display):
    cal_popup = ctk.CTkToplevel(form)
    cal_popup.title("Select Date")
    cal_popup.geometry("300x340")
    cal_popup.configure(fg_color="#f0f0f0")
    cal_popup.resizable(False, False)

    card = ctk.CTkFrame(cal_popup, corner_radius=16, fg_color="white", border_width=1, border_color="#e5e5e5")
    card.pack(padx=15, pady=15, fill="both", expand=True)

    today = date.today()
    state = {"year": today.year, "month": today.month}

    header_frame = ctk.CTkFrame(card, fg_color="transparent")
    header_frame.pack(pady=(20, 10))

    month_label = ctk.CTkLabel(header_frame, text="", font=("Arial", 16, "bold"), text_color="black")

    days_frame = ctk.CTkFrame(card, fg_color="transparent")
    days_frame.pack(pady=5)

    # draws the weekday headers and day grid for the currently selected month
    def render_calendar():
        for widget in days_frame.winfo_children():
            widget.destroy()

        month_label.configure(text=f"{calendar.month_name[state['month']]} {state['year']}")

        for col, name in enumerate(["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]):
            ctk.CTkLabel(days_frame, text=name, font=("Arial", 12, "bold"), text_color="#666666", width=36).grid(
                row=0, column=col, padx=2, pady=2
            )

        weeks = calendar.Calendar(firstweekday=0).monthdayscalendar(state["year"], state["month"])
        for row_index, week in enumerate(weeks, start=1):
            for col_index, day in enumerate(week):
                if day == 0:
                    continue

                def pick_day(d=day):
                    picked = date(state["year"], state["month"], d)
                    date_display.configure(text=picked.strftime("%Y-%m-%d"))
                    cal_popup.destroy()

                ctk.CTkButton(
                    days_frame,
                    text=str(day),
                    width=36,
                    height=36,
                    corner_radius=8,
                    fg_color="white",
                    text_color="black",
                    hover_color="#e0e0e0",
                    border_width=1,
                    border_color="#e5e5e5",
                    command=pick_day,
                ).grid(row=row_index, column=col_index, padx=2, pady=2)

    def go_prev_month():
        state["month"] -= 1
        if state["month"] == 0:
            state["month"] = 12
            state["year"] -= 1
        render_calendar()

    def go_next_month():
        state["month"] += 1
        if state["month"] == 13:
            state["month"] = 1
            state["year"] += 1
        render_calendar()

    prev_button = ctk.CTkButton(
        header_frame, text="◀", width=30, fg_color="#e0e0e0", text_color="black", hover_color="#cfcfcf", command=go_prev_month
    )
    prev_button.grid(row=0, column=0, padx=5)
    month_label.grid(row=0, column=1, padx=10)
    next_button = ctk.CTkButton(
        header_frame, text="▶", width=30, fg_color="#e0e0e0", text_color="black", hover_color="#cfcfcf", command=go_next_month
    )
    next_button.grid(row=0, column=2, padx=5)

    render_calendar()


# popup for entering a new task's name and due date
def open_add_task_form():
    form = ctk.CTkToplevel(app)
    form.title("Add Task")
    form.geometry("320x400")
    form.configure(fg_color="#f0f0f0")
    form.resizable(False, False)

    card = ctk.CTkFrame(form, corner_radius=16, fg_color="white", border_width=1, border_color="#e5e5e5")
    card.pack(padx=20, pady=20, fill="both", expand=True)

    title = ctk.CTkLabel(card, text="New Task", font=("Arial", 19, "bold"), text_color="black")
    title.pack(pady=(25, 20))

    name_label = ctk.CTkLabel(card, text="TASK NAME", font=("Arial", 11, "bold"), text_color="#999999")
    name_label.pack(anchor="w", padx=25)
    name_entry = ctk.CTkEntry(
        card,
        width=250,
        height=38,
        corner_radius=10,
        fg_color="#f7f7f7",
        border_width=1,
        border_color="#e0e0e0",
        placeholder_text="e.g. Buy groceries",
    )
    name_entry.pack(pady=(6, 20), padx=25)

    date_label = ctk.CTkLabel(card, text="DUE DATE", font=("Arial", 11, "bold"), text_color="#999999")
    date_label.pack(anchor="w", padx=25)

    date_row = ctk.CTkFrame(card, fg_color="#f7f7f7", corner_radius=10, border_width=1, border_color="#e0e0e0", height=38)
    date_row.pack(fill="x", padx=25, pady=(6, 25))
    date_row.pack_propagate(False)

    date_display = ctk.CTkLabel(date_row, text="No date selected", text_color="#999999", font=("Arial", 13))
    date_display.pack(side="left", padx=(12, 0))

    date_button = ctk.CTkButton(
        date_row,
        text="📅",
        width=32,
        height=28,
        corner_radius=8,
        fg_color="#e8ecf7",
        text_color="black",
        hover_color="#d6ddf0",
        command=lambda: open_calendar_popup(form, date_display),
    )
    date_button.pack(side="right", padx=5)

    save_button = ctk.CTkButton(
        card,
        text="Save Task",
        height=42,
        corner_radius=10,
        font=("Arial", 14, "bold"),
        fg_color="#2f5fdc",
        hover_color="#2549b0",
        command=lambda: save_new_task(form, name_entry, date_display),
    )
    save_button.pack(pady=(0, 25), padx=25, fill="x")



# picks a row color based on how soon a task is due
def get_priority_colors(due_date_str):
    try:
        due = date.fromisoformat(due_date_str)
    except ValueError:
        return "#f5f5f5", "#ececec"

    days_until = (due - date.today()).days
    if days_until <= 2:
        return "#f5b7b1", "#f0928c"
    if days_until <= 5:
        return "#f9e79f", "#f7d774"
    return "#a9dfbf", "#82c9a0"


# builds one clickable, hoverable row for a task
def create_task_row(parent, task):
    if task.get("completed", False):
        bg_color, hover_color = "#e0e0e0", "#d0d0d0"
    else:
        bg_color, hover_color = get_priority_colors(task["due_date"])

    row = ctk.CTkFrame(
        parent,
        height=70,
        corner_radius=10,
        fg_color=bg_color,
        border_width=1,
        border_color="#d0d0d0",
    )
    row.pack(pady=5, padx=5, fill="x")
    row.pack_propagate(False)

    name_label = ctk.CTkLabel(
        row, text=task["task_name"], font=("Arial", 17, "bold"), text_color="#777777" if task.get("completed", False) else "black"
    )
    name_label.place(x=15, y=12, anchor="nw")

    date_label = ctk.CTkLabel(row, text=task["due_date"], font=("Arial", 11), text_color="#a0a0a0")
    date_label.place(relx=1.0, rely=1.0, x=-15, y=-12, anchor="se")

    def on_enter(event, row=row):
        row.configure(fg_color=hover_color)

    def on_leave(event, row=row):
        row.configure(fg_color=bg_color)

    for widget in (row, name_label, date_label):
        widget.bind("<Button-1>", lambda event, t=task: open_edit_task_form(t))
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)


# redraws both task lists and their fixed headers
def render_tasks():
    for widget in pending_header_frame.winfo_children():
        widget.destroy()
    for widget in pending_list_frame.winfo_children():
        widget.destroy()
    for widget in completed_header_frame.winfo_children():
        widget.destroy()
    for widget in completed_list_frame.winfo_children():
        widget.destroy()

    tasks.sort(key=lambda task: task["due_date"])

    pending_tasks = [task for task in tasks if not task.get("completed", False)]
    completed_tasks = [task for task in tasks if task.get("completed", False)]

    total_count = len(pending_tasks) + len(completed_tasks)
    progress = len(completed_tasks) / total_count if total_count > 0 else 0

    progress_row = ctk.CTkFrame(pending_header_frame, fg_color="transparent")
    progress_row.pack(fill="x")

    ctk.CTkLabel(
        progress_row,
        text=f"{round(progress * 100)}% complete",
        font=("Arial", 12, "bold"),
        text_color="#666666",
    ).pack(side="left")

    ctk.CTkLabel(
        progress_row, text=f"{len(pending_tasks)} tasks", font=("Arial", 12, "bold"), text_color="#999999"
    ).pack(side="right")

    progress_bar = ctk.CTkProgressBar(pending_header_frame, progress_color="#2f5fdc")
    progress_bar.set(progress)
    progress_bar.pack(fill="x", pady=(4, 0))

    for task in pending_tasks:
        create_task_row(pending_list_frame, task)

    ctk.CTkLabel(
        completed_header_frame, text=f"{len(completed_tasks)} tasks", font=("Arial", 12, "bold"), text_color="#999999"
    ).pack(anchor="w")
    for task in completed_tasks:
        create_task_row(completed_list_frame, task)



# page title, centered at the top
title_label = ctk.CTkLabel(app, text="To Do List", font=("Arial", 24, "bold"), text_color="black")
title_label.place(relx=0.5, y=20, anchor="n")

# add task button, top right corner
add_task_button = ctk.CTkButton(
    app,
    text="+ Add Task",
    width=140,
    height=40,
    corner_radius=20,
    font=("Arial", 14, "bold"),
    fg_color="#2f5fdc",
    hover_color="#2549b0",
    command=open_add_task_form,
)
add_task_button.place(relx=1.0, x=-20, y=70, anchor="ne")

# pending/completed tabs
tasks_tabview = ctk.CTkTabview(
    app,
    width=460,
    height=440,
    corner_radius=10,
    fg_color="#f5f5f5",
    segmented_button_fg_color="#e5e5e5",
    segmented_button_selected_color="#2f5fdc",
    segmented_button_selected_hover_color="#2549b0",
    segmented_button_unselected_color="#e5e5e5",
    segmented_button_unselected_hover_color="#d5d5d5",
    segmented_button_font=("Arial", 15, "bold"),
    text_color="black",
    text_color_disabled="black",
)
tasks_tabview.place(relx=0.5, y=130, anchor="n")
tasks_tabview._segmented_button.configure(height=45)

tasks_tabview.add("Pending")
tasks_tabview.add("Completed")

# fixed header (progress + count) that stays visible while the pending list scrolls
pending_header_frame = ctk.CTkFrame(tasks_tabview.tab("Pending"), fg_color="transparent")
pending_header_frame.pack(fill="x", padx=10, pady=(10, 0))

pending_list_frame = ctk.CTkScrollableFrame(tasks_tabview.tab("Pending"), fg_color="transparent")
pending_list_frame.pack(padx=10, pady=(5, 10), fill="both", expand=True)

completed_header_frame = ctk.CTkFrame(tasks_tabview.tab("Completed"), fg_color="transparent")
completed_header_frame.pack(fill="x", padx=10, pady=(10, 0))

completed_list_frame = ctk.CTkScrollableFrame(tasks_tabview.tab("Completed"), fg_color="transparent")
completed_list_frame.pack(padx=10, pady=(5, 10), fill="both", expand=True)

render_tasks()


app.resizable(False, False)
app.mainloop()
