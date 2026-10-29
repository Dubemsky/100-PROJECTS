# Day 14 — Number Guessing Game

A number guessing game built with `customtkinter`. Pick a difficulty, guess the secret number, and use the temperature and possible numbers bars to zero in on it.

1. Choose Easy, Medium, or Hard from the selector — each has a different range and guess limit
2. Enter a guess and the game tells you if it's too low or too high, with a chip added to your guess history
3. The Temperature bar shows how close your last guess was, and Possible Numbers shows the range still left
4. Guess the number before you run out of guesses to beat your best score, saved per difficulty in `best_scores.json`
5. Stuck? Click Show me the trick to watch the perfect strategy (always guess the middle) play out

## How to run

Make sure you've completed the [setup steps](../README.md#setup) in the root folder first, then:

```
python3 main.py
```
