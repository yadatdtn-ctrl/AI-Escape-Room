"""Version 2: texts the player reads (same words as version1/texts.py).

PLACEHOLDERS: Yada will replace these with their own words. The code does not
need to change, only the texts in this file. (If you change them here, change
version1/texts.py too, or leave Version 1 as it was.)
"""

OPENING_TEXT = (
    "You wake up in a room you don't recognise. "
    "Pale sea light comes through a round window, and everything feels foggy, "
    "like an old photograph. A yellow raincoat hangs on a hook. "
    "There is a desk with a drawer, a small diary, a corkboard of photos, "
    "a record player on a shelf, and a door with a keypad.\n\n"
    "What do you do?"
)

# Shown when the interpreter fails (for example Gemini is busy). Nothing happens, no move is used.
TRY_AGAIN_TEXT = "The room flickers for a moment, and nothing happens. Please try again."

# The three memories that come back (cutscenes)
CUTSCENES = {
    1: {
        "title": "The Pier",
        "caption": "[PLACEHOLDER] Two friends laugh on a wooden pier at the festival, "
                   "taking silly photos with an old camera.",
    },
    2: {
        "title": "The Rooftop",
        "caption": "[PLACEHOLDER] A warm summer night. Two people lie on a rooftop, "
                   "looking up at the stars. Something quietly changes between them.",
    },
    3: {
        "title": "That Night",
        "caption": "[PLACEHOLDER] Rain. Raised voices. Red tail lights fade down the street. "
                   "Then only silence.",
    },
}

# Shown after the correct door code, above the two buttons
FINAL_CHOICE_TEXT = (
    "[PLACEHOLDER] The door opens onto white light. Behind you, the room is waiting. "
    "You can take Sky with you, or leave Sky here forever."
)

# Why the player lost (shown on the bad ending)
BAD_REASONS = {
    "time": "Time ran out.",
    "moves": "You used all your moves.",
    "codes": "The door locked after three wrong codes.",
}

# The three endings: "remember" and "forget" come from the final choice,
# "bad" comes from losing (time, moves or wrong codes).
ENDINGS = {
    "remember": {
        "title": "Remember",
        "text": "[PLACEHOLDER] You wake up and everything comes back at once: the pier, "
                "the rooftop, the rain. It hurts. But Sky is with you again, "
                "and you carry both the grief and the love.",
    },
    "forget": {
        "title": "Forget",
        "text": "[PLACEHOLDER] You wake up light and calm. Nothing hurts. "
                "Weeks later, a stranger's photo in a shop window makes you cry, "
                "and you don't know why.",
    },
    "bad": {
        "title": "The procedure erases too much",
        "text": "[PLACEHOLDER] The procedure does not stop. It takes Sky, and then it keeps "
                "going. You wake up in a bright room. A stranger's face looks back from the "
                "mirror. The last five years are gone: your friends, your home, your camera, "
                "your photos.",
    },
}
