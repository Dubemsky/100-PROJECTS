# Day 6 — Password Generator

A desktop password generator built with `customtkinter`, using the `secrets` module for cryptographically secure randomness.

1. Adjust the length slider and pick which character types to include (uppercase, lowercase, numbers, symbols), optionally excluding ambiguous characters
2. Click Generate — a strength meter (weak/medium/strong) shows below the password
3. Type a name (e.g. "Facebook", "Bank") and click Save to store it in `passwords.json`
4. Click "View Saved Passwords" to see everything you've saved, with a copy button for each

## How to run

Make sure you've completed the [setup steps](../README.md#setup) in the root folder first, then:

```
python3 main.py
```
