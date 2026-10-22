# Day 12 — Pomodoro Timer

A desktop Pomodoro timer built with `customtkinter`. Work in focused intervals, take breaks, and let the app guide the whole cycle for you.

1. Click Start to begin a 25 minute work session — the countdown and progress bar track the time left
2. Pause and resume anytime, or Reset to restart the current phase
3. When a phase ends, the timer auto-advances to the next one (Work → Short Break, repeated, then Work → Long Break every 4th session), with a system beep and a quick flash to let you know
4. The PHASE / SESSION pill at the top always shows where you are, e.g. "Work" and "3 / 4"
5. Click Durations to set your own work, short break, and long break lengths in minutes
6. Every completed work session is logged to `pomodoro_log.json` in this folder

## How to run

Make sure you've completed the [setup steps](../README.md#setup) in the root folder first, then:

```
python3 main.py
```
