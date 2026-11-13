"""Version 2: the game state (the notebook) and the config (the rulebook).

No Streamlit and no LLM in this file.
Only this file and validators.py are allowed to change the state.
"""
import json
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / "game_config.json"


def load_config(path=CONFIG_FILE):
    """Read the rulebook. Only Python reads it; it is never sent to the LLM."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def new_state(config):
    """A fresh game. (Streamlit adds the page-only fields in app.py.)"""
    return {
        "route": "main",          # prepared for the bonus route; only "main" now
        "moves": 0,               # every message = 1 move
        "wrong_codes": 0,         # wrong 4-digit codes typed at the door
        "inventory": [],          # item ids the player carries
        "revealed": [],           # item ids the player has seen (can take)
        "examined": [],           # object ids the player has examined
        "drawer_open": False,
        "record_played": False,   # the required puzzle: the third memory
        "door_open": False,       # True = escaped
        "cutscenes": [],          # numbers already played, e.g. [1, 2]
    }


def count_move(state):
    """Every player message costs one move."""
    state["moves"] += 1


def reveal(state, item_ids):
    """The player has seen these items, so they can be taken."""
    for item_id in item_ids:
        if item_id not in state["revealed"]:
            state["revealed"].append(item_id)


def add_item(state, item_id):
    state["inventory"].append(item_id)


def play_cutscene(state, number):
    """Return the cutscene number the first time, None if it was played before."""
    if number is None or number in state["cutscenes"]:
        return None
    state["cutscenes"].append(number)
    return number
