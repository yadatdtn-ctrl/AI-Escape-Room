"""Version 1: the limits of the game (time, moves, wrong door codes).

No Streamlit in this file, so it is easy to test with a plain dict.
"""
from settings import MAX_MOVES, MAX_WRONG_CODES


def time_is_up(state, now):
    """True if the clock ran out. 'now' is a time in seconds (time.time())."""
    return (not state["escaped"]) and now >= state["deadline"]


def check_limits(state):
    """Return why the player lost ("codes" or "moves"), or None if the game goes on."""
    if state["escaped"]:
        return None  # the player already opened the door
    if state["wrong_codes"] >= MAX_WRONG_CODES:
        return "codes"
    if state["moves"] >= MAX_MOVES:
        return "moves"
    return None
