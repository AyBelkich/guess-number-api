# Guess Number Game API 🎯

FastAPI version of my number guessing game.

## Features

- Start a game with difficulty and player name (`POST /start-game`)
- Make guesses using a game ID (`POST /check-guess`)
- Per-player stats (wins/losses) saved to `scores.txt`
- Clean separation between:
  - API endpoints (FastAPI)
  - game logic functions
  - stats load/save helpers

## Run locally

```bash
uvicorn main:app --reload
