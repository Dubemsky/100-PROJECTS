# Day 15 — Music Player

A desktop music player built with `customtkinter` and `pygame`, with a live FFT frequency visualizer.

1. Drop songs (`.mp3`, `.wav`, `.ogg`, `.flac`) into the `songs` folder, or click Open folder to pick another one
2. Play, pause, skip, and seek by dragging the progress bar — the visualizer reacts to whatever's playing
3. Toggle Shuffle (plays every song once before repeating) and Repeat (off / repeat all / repeat one)
4. Use keyboard shortcuts: Space to play/pause, Left/Right to seek 5s, Up/Down for volume, N/P for next/previous
5. Your folder, song, position, volume, shuffle, and repeat settings are remembered between sessions

## How to run

Make sure you've completed the [setup steps](../README.md#setup) in the root folder first, then:

```
python3 main.py
```
