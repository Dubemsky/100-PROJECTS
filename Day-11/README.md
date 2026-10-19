# Day 11 — Typing Speed Test

A desktop typing speed test built with `customtkinter`, with an on-screen keyboard and live letter-by-letter feedback, in the MonkeyType style — an endless stream of words rather than a fixed passage.

1. Start typing — the 30 second timer starts on your first keystroke
2. Each letter turns green (correct) or red (wrong) as you type, with a highlighted marker showing exactly where you are
3. The on-screen keyboard flashes the key you pressed, and Shift lights up while held
4. More words are generated automatically as you type, so you never run out
5. When the timer hits 0, your WPM (net, correct characters only) and accuracy are calculated
6. Click New Test to reset and try again — your best and last results are saved and shown below the keyboard

Scores are saved to `scores.json` in this folder.

## How to run

Make sure you've completed the [setup steps](../README.md#setup) in the root folder first, then:

```
python3 main.py
```
