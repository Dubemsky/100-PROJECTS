import json
import os
import random
import threading
import time
from tkinter import filedialog
 
import customtkinter as ctk
import numpy as np
import pygame
 
pygame.mixer.init(frequency=44100)
 
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")
 
app = ctk.CTk()
app.title("Music Player")
app.configure(fg_color="#eef0f8")
 
ACCENT_COLOR = "#4f46e5"
ACCENT_HOVER = "#4338ca"
TINT_COLOR = "#f3f4fd"
TINT_BORDER = "#e3e6fb"
TEXT_COLOR = "#1e1b3a"
MUTED_COLOR = "#8a88a8"
 
SONG_TYPES = (".mp3", ".wav", ".ogg", ".flac")
SAVE_FILE = "last_session.json"
SAMPLE_RATE = 44100
 
VISUALIZER_WIDTH = 440
VISUALIZER_HEIGHT = 140
BAR_COUNT = 28
UPDATE_MS = 33  # about 30 updates a second
 
songs_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "songs")
songs = []
current_index = -1
song_length = 0
song_samples = None  # the song as numbers, used by the visualiser
 
is_playing = False
play_started_at = 0  # time.time() when the song last started or resumed
start_position = 0  # where in the song (seconds) it last started from
is_dragging = False
 
shuffle_on = False
shuffle_deck = []  # songs left to play before any song repeats
history = []  # songs played so far, for the Previous button
 
REPEAT_MODES = ["off", "all", "one"]
repeat_mode = "all"
 
bar_heights = [0] * BAR_COUNT
tick_job = None
loudest_seen = 1.0
load_generation = 0  # invalidates a decode thread's result if a newer song was requested meanwhile
app_closing = False
is_loading = False  # True while a song is being decoded in the background
 
 
# ---------- loading songs ----------
 
def find_songs(folder):
    if not os.path.isdir(folder):
        return []
    names = [name for name in os.listdir(folder) if name.lower().endswith(SONG_TYPES)]
    return [os.path.join(folder, name) for name in sorted(names, key=str.lower)]
 
 
def song_name(path):
    return os.path.splitext(os.path.basename(path))[0]
 
 
def format_time(seconds):
    seconds = max(0, int(seconds))
    return f"{seconds // 60}:{seconds % 60:02d}"
 
 
def load_folder(folder):
    global songs_folder, songs, current_index, shuffle_deck, history
    stop()
    songs_folder = folder
    songs = find_songs(folder)
    current_index = -1
    shuffle_deck = []
    history = []
    draw_playlist()
    if songs:
        load_song(0)
    else:
        song_label.configure(text="No songs found")
        count_label.configure(text="Put MP3s in the songs folder or click Open folder")
        time_label.configure(text="0:00 / 0:00")
 
 
def open_folder():
    folder = filedialog.askdirectory(initialdir=songs_folder)
    if folder:
        load_folder(folder)
 
 
# decoding (for the visualiser) runs on a background thread so a big file doesn't freeze the UI;
# load_generation lets a stale result from a superseded request be ignored when it comes back
def load_song(index, position=0, autoplay=False):
    global load_generation, is_loading
    is_loading = True
    path = songs[index]
    load_generation += 1
    generation = load_generation
 
    song_label.configure(text=f"Loading {song_name(path)}…")
    count_label.configure(text=f"Song {index + 1} of {len(songs)}")
    time_label.configure(text="0:00 / 0:00")
 
    def decode():
        try:
            sound = pygame.mixer.Sound(path)
            length = sound.get_length()
            samples = pygame.sndarray.array(sound).astype(np.float32)
        except (pygame.error, OSError):
            if not app_closing:
                app.after(0, lambda: _song_load_failed(generation, index, autoplay))
            return
        if not app_closing:
            app.after(0, lambda: _song_loaded(generation, index, path, length, samples, position, autoplay))
 
    threading.Thread(target=decode, daemon=True).start()
 
 
def _song_loaded(generation, index, path, length, samples, position, autoplay):
    global current_index, song_length, song_samples, start_position, loudest_seen, is_loading
    if generation != load_generation:
        return
    is_loading = False
    try:
        pygame.mixer.music.load(path)
    except (pygame.error, OSError):
        _song_load_failed(generation, index, autoplay)
        return
 
    current_index = index
    song_length = length
    # a song you pick yourself counts as played in this shuffle round too
    if index in shuffle_deck:
        shuffle_deck.remove(index)
    song_samples = samples.mean(axis=1) if samples.ndim == 2 else samples
    loudest_seen = 1.0
    bar_heights[:] = [0] * BAR_COUNT
 
    start_position = min(position, song_length)
 
    song_label.configure(text=song_name(path))
    count_label.configure(text=f"Song {index + 1} of {len(songs)}")
    progress_slider.set(start_position / song_length if song_length else 0)
    update_time_label(start_position)
    draw_playlist()
 
    if autoplay:
        play_from(start_position)
        save_session()
 
 
# a file that matches the extension but won't decode: drop it and try the next one
def _song_load_failed(generation, index, autoplay):
    global current_index, is_loading, history, shuffle_deck
    if generation != load_generation:
        return
    is_loading = False
    if 0 <= index < len(songs):
        songs.pop(index)
        # every song after the broken one moves up a place, so fix the numbers we kept
        shift = lambda i: i - 1 if i > index else i
        history = [shift(i) for i in history if i != index]
        shuffle_deck = [shift(i) for i in shuffle_deck if i != index]
        if current_index == index:
            current_index = -1
        elif current_index > index:
            current_index -= 1
    if not songs:
        current_index = -1
        song_label.configure(text="No playable songs")
        count_label.configure(text="Couldn't load the songs in this folder")
        time_label.configure(text="0:00 / 0:00")
        draw_playlist()
        return
    load_song(index % len(songs), autoplay=autoplay)
 
 
# ---------- playing ----------
 
def current_position():
    if is_playing:
        return start_position + (time.time() - play_started_at)
    return start_position
 
 
def play_from(position):
    global is_playing, play_started_at, start_position
    start_position = max(0, min(position, song_length))
    try:
        pygame.mixer.music.play(start=start_position)
    except pygame.error:  # a few file types can't jump to a spot
        pygame.mixer.music.play()
        start_position = 0
    play_started_at = time.time()
    is_playing = True
    play_button.configure(text="❚❚")
 
 
def toggle_play():
    global is_playing, start_position
    if current_index < 0:
        return
    if is_playing:
        start_position = current_position()
        pygame.mixer.music.pause()
        is_playing = False
        play_button.configure(text="▶")
    else:
        play_from(start_position)
 
 
def stop():
    global is_playing
    pygame.mixer.music.stop()
    is_playing = False
    play_button.configure(text="▶")
 
 
def play_song(index):
    if current_index >= 0 and current_index != index:
        history.append(current_index)
    load_song(index, autoplay=True)
 
 
# smart shuffle: like a deck of cards, every song plays once before any song repeats
def next_shuffled_song():
    global shuffle_deck
    if len(songs) == 1:
        return current_index if repeat_mode != "off" else None
    if not shuffle_deck:
        if repeat_mode == "off":
            return None
        shuffle_deck = list(range(len(songs)))
        random.shuffle(shuffle_deck)
        # never play the same song twice in a row when a new round starts
        if shuffle_deck[-1] == current_index:
            shuffle_deck[0], shuffle_deck[-1] = shuffle_deck[-1], shuffle_deck[0]
    return shuffle_deck.pop()
 
 
def next_song():
    if not songs:
        return
    if shuffle_on:
        next_index = next_shuffled_song()
        if next_index is None:
            stop()
            return
        play_song(next_index)
    elif repeat_mode == "off" and current_index >= len(songs) - 1:
        stop()
    else:
        play_song((current_index + 1) % len(songs))
 
 
def previous_song():
    if not songs:
        return
    # a few seconds in, Previous restarts the song, like most music apps
    if current_position() > 3 or not history:
        play_from(0) if is_playing else restart_paused()
        return
    index = history.pop()
    load_song(index, autoplay=True)
 
 
def restart_paused():
    global start_position
    start_position = 0
    progress_slider.set(0)
    update_time_label(0)
 
 
def toggle_shuffle():
    global shuffle_on, shuffle_deck
    shuffle_on = not shuffle_on
    # the song playing now counts as already played in this round
    shuffle_deck = [i for i in range(len(songs)) if i != current_index]
    random.shuffle(shuffle_deck)
    shuffle_button.configure(
        fg_color=ACCENT_COLOR if shuffle_on else TINT_COLOR,
        text_color="white" if shuffle_on else TEXT_COLOR,
    )
    save_session()
 
 
def set_repeat_mode(mode):
    global repeat_mode
    repeat_mode = mode
    repeat_button.configure(
        text="↻¹" if repeat_mode == "one" else "↻",
        fg_color=ACCENT_COLOR if repeat_mode != "off" else TINT_COLOR,
        text_color="white" if repeat_mode != "off" else TEXT_COLOR,
    )
 
 
def toggle_repeat():
    set_repeat_mode(REPEAT_MODES[(REPEAT_MODES.index(repeat_mode) + 1) % len(REPEAT_MODES)])
    save_session()
 
 
def change_volume(value):
    pygame.mixer.music.set_volume(float(value))
 
 
def adjust_volume(delta):
    value = max(0, min(1, volume_slider.get() + delta))
    volume_slider.set(value)
    change_volume(value)
 
 
def seek_relative(delta):
    global start_position
    if current_index < 0:
        return
    position = max(0, min(current_position() + delta, song_length))
    if is_playing:
        play_from(position)
    else:
        start_position = position
        progress_slider.set(position / song_length if song_length else 0)
        update_time_label(position)
 
 
# ---------- progress bar ----------
 
def update_time_label(position):
    time_label.configure(text=f"{format_time(position)} / {format_time(song_length)}")
 
 
def start_drag(event=None):
    global is_dragging
    is_dragging = True
 
 
def while_dragging(value):
    if is_dragging:
        update_time_label(float(value) * song_length)
 
 
def end_drag(event=None):
    global is_dragging, start_position
    is_dragging = False
    if current_index < 0:
        return
    position = progress_slider.get() * song_length
    if is_playing:
        play_from(position)
    else:
        start_position = position
        update_time_label(position)
 
 
# ---------- visualiser ----------
 
def bar_levels(position):
    global loudest_seen
    window = 2048
    start = int(position * SAMPLE_RATE)
    chunk = song_samples[start:start + window] if song_samples is not None else np.zeros(0)
    if len(chunk) < window:
        chunk = np.pad(chunk, (0, window - len(chunk)))
 
    # split the sound into frequencies: low notes on the left, high notes on the right
    spectrum = np.abs(np.fft.rfft(chunk * np.hanning(window)))
    levels = np.array([spectrum[low:high].mean() for low, high in BAR_RANGES])
 
    # loudness in decibels, compared with the loudest moment so far
    loudest_seen = max(loudest_seen * 0.998, levels.max(), 1.0)
    decibels = 20 * np.log10(levels / loudest_seen + 1e-9)
    return np.clip((decibels + 50) / 50, 0, 1)  # -50 dB = empty bar, 0 dB = full bar
 
 
def make_bar_ranges():
    # each bar covers a slice of frequencies, spaced so bass and treble get fair room
    bins = np.fft.rfftfreq(2048, 1 / SAMPLE_RATE)
    edges = np.geomspace(60, 14000, BAR_COUNT + 1)
    ranges = []
    for low, high in zip(edges[:-1], edges[1:]):
        first = int(np.searchsorted(bins, low))
        last = max(first + 1, int(np.searchsorted(bins, high)))
        ranges.append((first, last))
    return ranges
 
 
BAR_RANGES = make_bar_ranges()
 
 
def draw_visualizer(position):
    target = bar_levels(position) if is_playing else np.zeros(BAR_COUNT)
    visualizer.delete("all")
    gap = 4
    bar_width = (VISUALIZER_WIDTH - gap * (BAR_COUNT + 1)) / BAR_COUNT
    for i in range(BAR_COUNT):
        # bars jump up fast and fall slowly, so they feel smooth
        if target[i] > bar_heights[i]:
            bar_heights[i] = target[i]
        else:
            bar_heights[i] = bar_heights[i] * 0.85 + target[i] * 0.15
        height = max(4, bar_heights[i] * (VISUALIZER_HEIGHT - 16))
        x = gap + i * (bar_width + gap)
        color = BAR_COLORS[min(len(BAR_COLORS) - 1, int(bar_heights[i] * len(BAR_COLORS)))]
        visualizer.create_rectangle(
            x, VISUALIZER_HEIGHT - 8 - height, x + bar_width, VISUALIZER_HEIGHT - 8, fill=color, outline=""
        )
 
 
BAR_COLORS = ["#6366f1", "#7c6cf2", "#9b6cf0", "#c26ae6", "#e86ad0", "#f472b6"]
 
 
# ---------- the main loop ----------
 
def tick():
    if current_index >= 0:
        position = current_position()
        if is_playing and not is_dragging and not is_loading and position >= song_length - 0.05:
            if repeat_mode == "one":
                play_from(0)
            else:
                next_song()
            position = 0
        if not is_dragging and song_length:
            progress_slider.set(min(1, position / song_length))
            update_time_label(position)
        draw_visualizer(position)
    global tick_job
    tick_job = app.after(UPDATE_MS, tick)
 
 
# ---------- remembering the last song ----------
 
def save_session():
    data = {
        "folder": songs_folder,
        "song": songs[current_index] if 0 <= current_index < len(songs) else None,
        "position": round(current_position(), 1),
        "volume": round(volume_slider.get(), 2),
        "shuffle": shuffle_on,
        "repeat": repeat_mode,
    }
    with open(SAVE_FILE, "w") as file:
        json.dump(data, file, indent=2)
 
 
def load_session():
    if not os.path.exists(SAVE_FILE):
        return {}
    try:
        with open(SAVE_FILE, "r") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return {}
 
 
def on_close():
    global app_closing
    app_closing = True
    if current_index >= 0:
        save_session()
    app.after_cancel(tick_job)
    pygame.mixer.music.stop()
    app.destroy()
 
 
# ---------- playlist ----------
 
def draw_playlist():
    for row in playlist_frame.winfo_children():
        row.destroy()
    for index, path in enumerate(songs):
        is_current = index == current_index
        ctk.CTkButton(
            playlist_frame, text=f"{index + 1}.  {song_name(path)}", anchor="w", height=34, corner_radius=10,
            font=("Helvetica", 13, "bold"),
            fg_color=ACCENT_COLOR if is_current else "transparent",
            hover_color=ACCENT_HOVER if is_current else TINT_BORDER,
            text_color="white" if is_current else TEXT_COLOR,
            command=lambda i=index: play_song(i),
        ).pack(fill="x", padx=4, pady=2)
 
 
# ---------- the window ----------
 
card = ctk.CTkFrame(app, corner_radius=22, fg_color="white", border_width=1, border_color=TINT_BORDER)
card.pack(padx=28, pady=20)
 
ctk.CTkLabel(card, text="Music Player", font=("Georgia", 22, "bold"), text_color=TEXT_COLOR).pack(pady=(20, 2))
ctk.CTkLabel(card, text="Your songs, one folder", font=("Helvetica", 11), text_color=MUTED_COLOR).pack(pady=(0, 12))
 
visualizer_card = ctk.CTkFrame(card, corner_radius=16, fg_color="#151338")
visualizer_card.pack(padx=28)
visualizer = ctk.CTkCanvas(visualizer_card, width=VISUALIZER_WIDTH, height=VISUALIZER_HEIGHT, bg="#151338", highlightthickness=0)
visualizer.pack(padx=10, pady=10)
 
song_label = ctk.CTkLabel(card, text="", font=("Georgia", 20, "bold"), text_color=TEXT_COLOR)
song_label.pack(padx=28, pady=(16, 0))
count_label = ctk.CTkLabel(card, text="", font=("Helvetica", 12, "bold"), text_color=MUTED_COLOR)
count_label.pack()
 
progress_slider = ctk.CTkSlider(
    card, from_=0, to=1, width=460, height=18, command=while_dragging,
    progress_color=ACCENT_COLOR, button_color=ACCENT_COLOR, button_hover_color=ACCENT_HOVER, fg_color=TINT_BORDER,
)
progress_slider.set(0)
progress_slider.pack(padx=28, pady=(14, 0))
progress_slider.bind("<ButtonPress-1>", start_drag, add="+")
progress_slider.bind("<ButtonRelease-1>", end_drag, add="+")
 
time_label = ctk.CTkLabel(card, text="0:00 / 0:00", font=("Helvetica", 12, "bold"), text_color=MUTED_COLOR)
time_label.pack()
 
controls = ctk.CTkFrame(card, fg_color="transparent")
controls.pack(pady=(8, 4))
 
shuffle_button = ctk.CTkButton(
    controls, text="⤨", width=44, height=44, corner_radius=22, font=("Helvetica", 18, "bold"),
    fg_color=TINT_COLOR, hover_color=TINT_BORDER, text_color=TEXT_COLOR, command=toggle_shuffle,
)
shuffle_button.grid(row=0, column=0, padx=8)
 
small_button = dict(width=52, height=52, corner_radius=26, font=("Helvetica", 18, "bold"),
                    fg_color=TINT_COLOR, hover_color=TINT_BORDER, text_color=TEXT_COLOR)
ctk.CTkButton(controls, text="⏮", command=previous_song, **small_button).grid(row=0, column=1, padx=6)
play_button = ctk.CTkButton(
    controls, text="▶", width=72, height=72, corner_radius=36, font=("Helvetica", 24, "bold"),
    fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER, command=toggle_play,
)
play_button.grid(row=0, column=2, padx=6)
ctk.CTkButton(controls, text="⏭", command=next_song, **small_button).grid(row=0, column=3, padx=6)
 
repeat_button = ctk.CTkButton(
    controls, text="↻", width=44, height=44, corner_radius=22, font=("Helvetica", 20, "bold"),
    fg_color=TINT_COLOR, hover_color=TINT_BORDER, text_color=TEXT_COLOR, command=toggle_repeat,
)
repeat_button.grid(row=0, column=4, padx=8)
 
volume_row = ctk.CTkFrame(card, fg_color="transparent")
volume_row.pack(pady=(6, 4))
ctk.CTkLabel(volume_row, text="Volume", font=("Helvetica", 11, "bold"), text_color=MUTED_COLOR).pack(side="left", padx=(0, 10))
volume_slider = ctk.CTkSlider(
    volume_row, from_=0, to=1, width=200, height=14, command=change_volume,
    progress_color=ACCENT_COLOR, button_color=ACCENT_COLOR, button_hover_color=ACCENT_HOVER, fg_color=TINT_BORDER,
)
volume_slider.pack(side="left")
 
playlist_header = ctk.CTkFrame(card, fg_color="transparent")
playlist_header.pack(padx=28, pady=(12, 0), fill="x")
ctk.CTkLabel(playlist_header, text="PLAYLIST", font=("Helvetica", 10, "bold"), text_color=MUTED_COLOR).pack(side="left")
ctk.CTkButton(
    playlist_header, text="Open folder", width=110, height=28, corner_radius=10, font=("Helvetica", 12, "bold"),
    fg_color="transparent", text_color=ACCENT_COLOR, hover_color=TINT_COLOR, border_width=1.5, border_color=ACCENT_COLOR,
    command=open_folder,
).pack(side="right")
 
playlist_frame = ctk.CTkScrollableFrame(card, width=440, height=170, corner_radius=14, fg_color=TINT_COLOR,
                                        border_width=1, border_color=TINT_BORDER)
playlist_frame.pack(padx=28, pady=(8, 22))
 
 
# ---------- start ----------
 
session = load_session()
volume_slider.set(session.get("volume", 0.7))
change_volume(volume_slider.get())
saved_folder = session.get("folder")
load_folder(saved_folder if saved_folder and os.path.isdir(saved_folder) else songs_folder)
 
# pick up where you left off: same song, same spot, paused
if session.get("song") in songs:
    load_song(songs.index(session["song"]), session.get("position", 0))
if session.get("shuffle"):
    toggle_shuffle()
set_repeat_mode(session.get("repeat", "all"))
 
app.bind("<space>", lambda event: toggle_play())
app.bind("<Right>", lambda event: seek_relative(5))
app.bind("<Left>", lambda event: seek_relative(-5))
app.bind("<Up>", lambda event: adjust_volume(0.05))
app.bind("<Down>", lambda event: adjust_volume(-0.05))
app.bind("n", lambda event: next_song())
app.bind("p", lambda event: previous_song())
 
app.protocol("WM_DELETE_WINDOW", on_close)
app.resizable(False, False)
tick()
app.mainloop()
