"""Version 1: find the hidden tags in the Game Master's answer and apply them.

Gemini writes tags like [[ITEM:brass_key]] at the end of its answer.
The player never sees them: we cut them out and use them to update the game.
"""
import re

# Matches [[NAME]] or [[NAME:value]]
TAG_PATTERN = re.compile(r"\[\[([A-Z_]+)(?::([A-Za-z0-9_]+))?\]\]")

# Items the player can carry, and how we show their names
ITEM_NAMES = {"brass_key": "brass key", "vinyl_record": "vinyl record"}


def parse_tags(text):
    """Return (clean_text, tags). tags looks like [("ITEM", "brass_key")]."""
    tags = TAG_PATTERN.findall(text)
    clean = TAG_PATTERN.sub("", text)
    clean = re.sub(r"\n{3,}", "\n\n", clean).strip()
    return clean, tags


def apply_tags(tags, state):
    """Change the game state according to the tags.

    state needs: inventory (list), cutscenes (list), wrong_codes (int), escaped (bool).
    Returns the numbers of cutscenes that are NEW (seen for the first time).
    """
    new_cutscenes = []
    for name, value in tags:
        if name == "ITEM" and value in ITEM_NAMES:
            if value not in state["inventory"]:
                state["inventory"].append(value)
        elif name == "CUTSCENE" and value in ("1", "2", "3"):
            if int(value) not in state["cutscenes"]:
                state["cutscenes"].append(int(value))
                new_cutscenes.append(int(value))
        elif name == "WRONG_DOOR":
            state["wrong_codes"] += 1
        elif name == "ESCAPED":
            state["escaped"] = True
        # Any other tag is ignored on purpose
    return new_cutscenes
