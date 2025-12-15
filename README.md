# Guess the Number – FastAPI Backend (guessnumber_api)

This is the **API backend** for my “Guess the Number” game.

It’s a FastAPI application that exposes HTTP endpoints to:

- start a guessing game,
- send guesses and get feedback (`too_high`, `too_low`, `win`, `lose`),
- track per-player wins and losses.

I originally built this as a CLI Python game, then refactored the logic into an HTTP API so it could be used by different clients (like a web frontend). I used an AI assistant (ChatGPT) a lot for explanations, refactoring, and debugging, but I worked through the structure and logic myself step by step.

## Features

- **Start game with difficulty & player name**
  - Difficulty levels:
    - `1` – Easy: 1–10, 5 attempts
    - `2` – Medium: 1–20, 4 attempts
    - `3` – Hard: 1–50, 3 attempts
  - Returns a `game_id`, `number_range`, and `max_attempts`.

- **Check guesses via API**
  - Endpoint accepts `game_id` + `guess`.
  - Responds with:
    - `too_high`
    - `too_low`
    - `win`
    - `lose`
    - `game_over` (if you try to guess after game finished)
  - Tracks remaining attempts.

- **Per-player stats**
  - Persistent stats in `scores.txt`:
    - total `wins`
    - total `losses`
  - Each completed game updates the player’s record.
  - Stats available via a separate endpoint.

- **In-memory game sessions**
  - Games are stored in a Python dict (`games`) in memory:
    - `secret_number`
    - `number_range`
    - `max_attempts`
    - `attempts_used`
    - `is_over`
    - `player_name`

- **CORS support**
  - CORS middleware is enabled so a browser frontend can call the API from a different origin (e.g. from `index.html` opened locally).

## Tech Stack

- **Language:** Python 3
- **Framework:** FastAPI
- **Server:** Uvicorn
- **Validation:** Pydantic models
- **Data persistence:** simple file (`scores.txt`)
- **Containerization:** Docker (with a `Dockerfile`)
- **Cloud (tested on):**
  - Local machine
  - Docker Desktop
  - AWS EC2 (Amazon Linux)
  - Azure Virtual Machine (Ubuntu)
  - Azure App Service – Web App for Containers

## Project Structure

Typical structure of the API project:

  guessnumber_api/
  ├─ main.py          # FastAPI app
  ├─ requirements.txt # Python dependencies
  ├─ Dockerfile       # Container build instructions
  └─ scores.txt       # Created/updated at runtime to store stats
