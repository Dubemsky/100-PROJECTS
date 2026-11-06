# Day 16 — Snake Game

A desktop Snake game built with `pygame`. Play it yourself, or switch on the autopilot and watch the snake play on its own at one of three levels.

1. Move with the arrow keys, eat the red apples to grow, and avoid the walls and your own body
2. Press A to switch the autopilot on or off, or press 1, 2, or 3 to pick a level
3. Level 1 heads straight for the apple without checking its own body, so it eventually crashes into itself
4. Level 2 searches for a route to the apple that avoids its body and draws it as a line — it lasts much longer, but can still trap itself
5. Level 3 only goes for the apple if it could still reach its tail afterwards, and otherwise follows its tail (orange line). If it circles for too long it takes a risk (red line), and it usually fills almost the whole board
6. Press + or - to change the speed, Space to pause, R to restart, and M to turn the sound on or off
7. Best scores are saved to `best_scores.json` separately for you and each autopilot level — a game played in more than one mode doesn't count

## How to run

Make sure you've completed the [setup steps](../README.md#setup) in the root folder first, then:

```
python3 main.py
```
