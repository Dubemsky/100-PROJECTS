import json
import os
from datetime import datetime
import customtkinter as ctk

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Pomodoro Timer")
app.configure(fg_color="#eef0f8")

ACCENT_COLOR = "#4f46e5"
ACCENT_HOVER = "#4338ca"
TINT_COLOR = "#f3f4fd"
TINT_BORDER = "#e3e6fb"

WORK_DURATION = 25 * 60
SHORT_BREAK_DURATION = 5 * 60
LONG_BREAK_DURATION = 15 * 60
SESSIONS_PER_CYCLE = 4

PHASE_DURATIONS = {"work": WORK_DURATION, "short_break": SHORT_BREAK_DURATION, "long_break": LONG_BREAK_DURATION}
PHASE_LABELS = {"work": "Work", "short_break": "Short Break", "long_break": "Long Break"}

LOG_FILE = "pomodoro_log.json"

current_phase = "work"
session_count = 1
current_phase_duration = WORK_DURATION
time_remaining = WORK_DURATION
is_running = False
timer_generation = 0


# load the completed-pomodoro log from the json file, or start fresh if it's missing or empty
def load_log():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r") as file:
        content = file.read().strip()
        return json.loads(content) if content else []


# save the completed-pomodoro log back to the json file
def save_log():
    with open(LOG_FILE, "w") as file:
        json.dump(pomodoro_log, file, indent=2)


pomodoro_log = load_log()


# records a just-finished work session to the log
def log_completed_pomodoro():
    pomodoro_log.append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%H:%M"),
        "duration_minutes": current_phase_duration // 60,
    })
    save_log()

# updates the countdown text and progress bar to match time_remaining
def update_display():
    minutes, seconds = divmod(time_remaining, 60)
    timer_label.configure(text=f"{minutes:02d}:{seconds:02d}")
    progress_bar.set(time_remaining / current_phase_duration)

# moves to the next phase in the work -> short break -> ... -> long break cycle
def advance_phase():
    global current_phase, session_count, time_remaining, current_phase_duration

    if current_phase == "work":
        log_completed_pomodoro()
        current_phase = "long_break" if session_count >= SESSIONS_PER_CYCLE else "short_break"
    elif current_phase == "short_break":
        current_phase = "work"
        session_count += 1
    elif current_phase == "long_break":
        current_phase = "work"
        session_count = 1

    current_phase_duration = PHASE_DURATIONS[current_phase]
    time_remaining = current_phase_duration

    phase_label.configure(text=PHASE_LABELS[current_phase])
    session_label.configure(text=f"{session_count} / {SESSIONS_PER_CYCLE}")
    update_display()
    notify_phase_end()

# plays the system alert sound and double-flashes the timer box
def notify_phase_end():
    app.bell()

    def flash_on():
        timer_frame.configure(fg_color=ACCENT_COLOR)
        timer_label.configure(text_color="white")

    def flash_off():
        timer_frame.configure(fg_color=TINT_COLOR)
        timer_label.configure(text_color="#1e1b3a")

    flash_on()
    app.after(150, flash_off)
    app.after(300, flash_on)
    app.after(450, flash_off)

# ticks the countdown down by one second, auto-advancing to the next phase once it hits 0
# "generation" guards against a stale tick from a prior start/pause/resume cycle still running
def tick(generation):
    global time_remaining, is_running

    if not is_running or generation != timer_generation:
        return

    time_remaining -= 1

    if time_remaining <= 0:
        advance_phase()
    else:
        update_display()

    app.after(1000, lambda gen=generation: tick(gen))

# starts (or resumes) the countdown from wherever it currently is
def start_timer():
    global is_running, timer_generation
    if is_running:
        return
    is_running = True
    timer_generation += 1
    app.after(1000, lambda gen=timer_generation: tick(gen))

# pauses the countdown, leaving time_remaining where it is
def pause_timer():
    global is_running
    is_running = False

# stops the countdown and resets the current phase back to its full duration
def reset_timer():
    global time_remaining, is_running
    is_running = False
    time_remaining = current_phase_duration
    update_display()

# popup for setting how long each phase lasts, in minutes
def open_duration_settings():
    form = ctk.CTkToplevel(app)
    form.title("Durations")
    form.geometry("300x400")
    form.configure(fg_color="#eef0f8")
    form.resizable(False, False)

    card = ctk.CTkFrame(form, corner_radius=20, fg_color="white", border_width=1, border_color="#e5e7f5")
    card.pack(padx=20, pady=20, fill="both", expand=True)

    ctk.CTkLabel(card, text="Durations", font=("Georgia", 18, "bold"), text_color="#1e1b3a").pack(pady=(20, 16))

    ctk.CTkLabel(card, text="WORK (MINUTES)", font=("Arial", 10, "bold"), text_color="#9796b8").pack(anchor="w", padx=20)
    work_entry = ctk.CTkEntry(card, height=36, corner_radius=10, fg_color=TINT_COLOR, border_width=1, border_color=TINT_BORDER)
    work_entry.insert(0, str(PHASE_DURATIONS["work"] // 60))
    work_entry.pack(padx=20, pady=(4, 12), fill="x")

    ctk.CTkLabel(card, text="SHORT BREAK (MINUTES)", font=("Arial", 10, "bold"), text_color="#9796b8").pack(anchor="w", padx=20)
    short_entry = ctk.CTkEntry(card, height=36, corner_radius=10, fg_color=TINT_COLOR, border_width=1, border_color=TINT_BORDER)
    short_entry.insert(0, str(PHASE_DURATIONS["short_break"] // 60))
    short_entry.pack(padx=20, pady=(4, 12), fill="x")

    ctk.CTkLabel(card, text="LONG BREAK (MINUTES)", font=("Arial", 10, "bold"), text_color="#9796b8").pack(anchor="w", padx=20)
    long_entry = ctk.CTkEntry(card, height=36, corner_radius=10, fg_color=TINT_COLOR, border_width=1, border_color=TINT_BORDER)
    long_entry.insert(0, str(PHASE_DURATIONS["long_break"] // 60))
    long_entry.pack(padx=20, pady=(4, 16), fill="x")

    save_button = ctk.CTkButton(
        card,
        text="Save",
        height=38,
        corner_radius=14,
        font=("Arial", 14, "bold"),
        fg_color=ACCENT_COLOR,
        hover_color=ACCENT_HOVER,
        command=lambda: save_durations(form, work_entry, short_entry, long_entry),
    )
    save_button.pack(padx=20, fill="x")

# validates and saves the new phase durations, refreshing the display if nothing is running
def save_durations(form, work_entry, short_entry, long_entry):
    global current_phase_duration, time_remaining

    entries = {"work": work_entry, "short_break": short_entry, "long_break": long_entry}
    new_durations = {}

    for phase, entry in entries.items():
        entry.configure(border_color=TINT_BORDER)
        try:
            minutes = int(entry.get().strip())
            if minutes <= 0:
                raise ValueError
            new_durations[phase] = minutes * 60
        except ValueError:
            entry.configure(border_color="#ef4444")
            return

    PHASE_DURATIONS.update(new_durations)

    if not is_running:
        current_phase_duration = PHASE_DURATIONS[current_phase]
        time_remaining = current_phase_duration
        update_display()

    form.destroy()



# white card floating on the light tinted background
card = ctk.CTkFrame(app, corner_radius=22, fg_color="white", border_width=1, border_color="#e5e7f5")
card.pack(padx=18, pady=18)

title_label = ctk.CTkLabel(card, text="Pomodoro Timer", font=("Georgia", 22, "bold"), text_color="#1e1b3a")
title_label.pack(pady=(22, 2))

subtitle_label = ctk.CTkLabel(card, text="Stay focused, one session at a time", font=("Arial", 11), text_color="#9796b8")
subtitle_label.pack(pady=(0, 10))

durations_button = ctk.CTkButton(
    card,
    text="⚙  Durations",
    width=130,
    height=30,
    corner_radius=12,
    font=("Arial", 12, "bold"),
    fg_color="transparent",
    text_color=ACCENT_COLOR,
    hover_color=TINT_COLOR,
    border_width=1.5,
    border_color=ACCENT_COLOR,
    command=open_duration_settings,
)
durations_button.pack(pady=(0, 16))

# phase pill: phase / session
phase_frame = ctk.CTkFrame(card, corner_radius=16, fg_color=ACCENT_COLOR)
phase_frame.pack(padx=20, pady=(0, 14), fill="x")

phase_column = ctk.CTkFrame(phase_frame, fg_color="transparent")
phase_column.pack(side="left", expand=True, fill="x", pady=4)
ctk.CTkLabel(phase_column, text="PHASE", font=("Arial", 9, "bold"), text_color="#c9c4f7").pack()
phase_label = ctk.CTkLabel(phase_column, text="Work", font=("Georgia", 16, "bold"), text_color="white")
phase_label.pack()

divider = ctk.CTkFrame(phase_frame, width=1, height=1, fg_color="#7a71ea")
divider.pack(side="left", fill="y", pady=4)

session_column = ctk.CTkFrame(phase_frame, fg_color="transparent")
session_column.pack(side="left", expand=True, fill="x", pady=4)
ctk.CTkLabel(session_column, text="SESSION", font=("Arial", 9, "bold"), text_color="#c9c4f7").pack()
session_label = ctk.CTkLabel(session_column, text="1 / 4", font=("Georgia", 16, "bold"), text_color="white")
session_label.pack()

timer_frame = ctk.CTkFrame(card, corner_radius=16, fg_color=TINT_COLOR, border_width=1, border_color=TINT_BORDER)
timer_frame.pack(padx=20, pady=(0, 14), fill="x")

timer_label = ctk.CTkLabel(timer_frame, text="25:00", font=("Georgia", 48, "bold"), text_color="#1e1b3a")
timer_label.pack(pady=(24, 10))

progress_bar = ctk.CTkProgressBar(timer_frame, progress_color=ACCENT_COLOR, fg_color=TINT_BORDER)
progress_bar.set(1.0)
progress_bar.pack(padx=30, pady=(0, 24), fill="x")

controls_frame = ctk.CTkFrame(card, fg_color="transparent")
controls_frame.pack(padx=20, pady=(0, 20), fill="x")

start_button = ctk.CTkButton(
    controls_frame,
    text="Start",
    height=38,
    corner_radius=14,
    font=("Arial", 14, "bold"),
    fg_color=ACCENT_COLOR,
    hover_color=ACCENT_HOVER,
    command=start_timer,
)
start_button.pack(side="left", expand=True, fill="x", padx=(0, 6))

pause_button = ctk.CTkButton(
    controls_frame,
    text="Pause",
    height=38,
    corner_radius=14,
    font=("Arial", 14, "bold"),
    fg_color=TINT_COLOR,
    text_color="#1e1b3a",
    hover_color=TINT_BORDER,
    border_width=1,
    border_color=TINT_BORDER,
    command=pause_timer,
)
pause_button.pack(side="left", expand=True, fill="x", padx=6)

reset_button = ctk.CTkButton(
    controls_frame,
    text="Reset",
    height=38,
    corner_radius=14,
    font=("Arial", 14, "bold"),
    fg_color=TINT_COLOR,
    text_color="#1e1b3a",
    hover_color=TINT_BORDER,
    border_width=1,
    border_color=TINT_BORDER,
    command=reset_timer,
)
reset_button.pack(side="left", expand=True, fill="x", padx=(6, 0))


app.resizable(False, False)
app.mainloop()
