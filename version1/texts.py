"""Texts the player reads at the end.

PLACEHOLDERS: Yada will replace these with their own words. The code does not
need to change, only the texts in this file.
"""

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

BAD_ENDING_TITLE = "The procedure erases too much"

# Why the player lost (shown above the ending text)
BAD_REASONS = {
    "time": "Time ran out.",
    "moves": "You used all your moves.",
    "codes": "The door locked after three wrong codes.",
}

BAD_ENDING_TEXT = (
    "[PLACEHOLDER] The procedure does not stop. It takes Sky, and then it keeps going. "
    "You wake up in a bright room. A stranger's face looks back from the mirror. "
    "The last five years are gone: your friends, your home, your camera, your photos."
)
