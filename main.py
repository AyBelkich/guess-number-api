from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
import uuid

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for learning: allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- In-memory state ----------

games = {}  # game_id -> game dict
stats = {}  # player_name -> {"wins": int, "losses": int}


# ---------- Pydantic models (request/response) ----------

class GreetRequest(BaseModel):
    name: str


class GuessResponse(BaseModel):
    result: str           # "too_high", "too_low", "win", "lose", "game_over"
    attempts_left: int
    correct_number: int | None = None  # filled only when game is over


class GuessCheckRequest(BaseModel):
    game_id: str
    guess: int


class StartGameRequest(BaseModel):
    difficulty: int
    player_name: str


class StartGameResponse(BaseModel):
    game_id: str
    number_range: int
    max_attempts: int


# ---------- Stats helpers (load/save/update) ----------

def load_stats() -> dict:
    data = {}
    try:
        with open("scores.txt", "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                name, wins_str, losses_str = line.split(";")
                data[name] = {
                    "wins": int(wins_str),
                    "losses": int(losses_str),
                }
    except FileNotFoundError:
        # first run: file doesn't exist yet
        pass
    return data


def save_stats() -> None:
    with open("scores.txt", "w") as f:
        for name, record in stats.items():
            f.write("%s;%d;%d\n" % (name, record["wins"], record["losses"]))


def ensure_player_stats(player_name: str) -> None:
    if player_name not in stats:
        stats[player_name] = {"wins": 0, "losses": 0}


def record_result(player_name: str, result: str) -> None:
    ensure_player_stats(player_name)
    if result == "win":
        stats[player_name]["wins"] += 1
    elif result == "lose":
        stats[player_name]["losses"] += 1
    save_stats()


# load stats at startup
stats = load_stats()


# ---------- Core game logic helpers (pure-ish) ----------

def check_guess(secret_number: int, guess: int) -> str:
    if guess > secret_number:
        return "too_high"
    elif guess < secret_number:
        return "too_low"
    else:
        return "correct"


def choose_difficulty_from_number(difficulty: int) -> tuple[int, int]:
    if difficulty == 1:
        return 10, 5
    elif difficulty == 2:
        return 20, 4
    elif difficulty == 3:
        return 50, 3
    else:
        raise ValueError("Invalid difficulty")


# ---------- Game service functions (use globals games/stats) ----------

def create_game(difficulty: int, player_name: str) -> StartGameResponse:
    try:
        number_range, max_attempts = choose_difficulty_from_number(difficulty)
    except ValueError:
        # let the endpoint decide the HTTP error
        raise

    secret_number = random.randint(1, number_range)
    game_id = uuid.uuid4().hex

    ensure_player_stats(player_name)

    games[game_id] = {
        "secret_number": secret_number,
        "number_range": number_range,
        "max_attempts": max_attempts,
        "attempts_used": 0,
        "is_over": False,
        "player_name": player_name,
    }

    return StartGameResponse(
        game_id=game_id,
        number_range=number_range,
        max_attempts=max_attempts,
    )


def get_game_or_404(game_id: str) -> dict:
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    return games[game_id]


def apply_guess_to_game(game: dict, guess: int) -> GuessResponse:
    # game already over?
    if game["is_over"]:
        return GuessResponse(
            result="game_over",
            attempts_left=game["max_attempts"] - game["attempts_used"],
            correct_number=game["secret_number"],
        )

    # validate guess range
    if guess < 1 or guess > game["number_range"]:
        raise HTTPException(
            status_code=400,
            detail=f"Guess must be between 1 and {game['number_range']}",
        )

    # count this attempt
    game["attempts_used"] += 1

    basic_result = check_guess(game["secret_number"], guess)
    attempts_left = game["max_attempts"] - game["attempts_used"]

    # handle win
    if basic_result == "correct":
        game["is_over"] = True
        player_name = game["player_name"]
        record_result(player_name, "win")
        return GuessResponse(
            result="win",
            attempts_left=attempts_left,
            correct_number=game["secret_number"],
        )

    # handle lose (no attempts left and not correct)
    if attempts_left <= 0:
        game["is_over"] = True
        player_name = game["player_name"]
        record_result(player_name, "lose")
        return GuessResponse(
            result="lose",
            attempts_left=0,
            correct_number=game["secret_number"],
        )

    # still going: just too high / too low
    return GuessResponse(
        result=basic_result,  # "too_high" or "too_low"
        attempts_left=attempts_left,
        correct_number=None,
    )


def get_player_stats_data(player_name: str) -> dict:
    if player_name not in stats:
        raise HTTPException(status_code=404, detail="Player not found")
    return {
        "player_name": player_name,
        "wins": stats[player_name]["wins"],
        "losses": stats[player_name]["losses"],
    }


# ---------- Endpoints (thin controllers) ----------

@app.get("/")
def read_root():
    return {"message": "Hello, this is my first API!"}


@app.post("/greet")
def greet(request: GreetRequest):
    return {"message": f"Hello, {request.name}!"}


@app.post("/start-game", response_model=StartGameResponse)
def start_game(req: StartGameRequest):
    try:
        return create_game(req.difficulty, req.player_name)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid difficulty. Use 1, 2, or 3.")


@app.post("/check-guess", response_model=GuessResponse)
def check_guess_endpoint(request: GuessCheckRequest):
    game = get_game_or_404(request.game_id)
    return apply_guess_to_game(game, request.guess)


@app.get("/stats/{player_name}")
def get_player_stats(player_name: str):
    return get_player_stats_data(player_name)
