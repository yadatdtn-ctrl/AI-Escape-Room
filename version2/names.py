"""Version 2: the player's name. No Streamlit and no LLM in this file.

The name is typed by the player, so it is untrusted text. clean_name() keeps only a short,
harmless word. The name is used ONLY in fixed texts (see address()); it never goes to the LLM.
"""

MAX_NAME_LENGTH = 12
ALLOWED_MARKS = "-'"  # a name may have a hyphen or an apostrophe, like Anne-Marie or O'Neil


def clean_name(raw):
    """The first word of what was typed: only letters, - and ', at most 12 characters."""
    if not isinstance(raw, str) or not raw.split():
        return ""
    word = raw.split()[0]  # only the first word
    word = "".join(ch for ch in word if ch.isalpha() or ch in ALLOWED_MARKS)
    word = word.strip(ALLOWED_MARKS)[:MAX_NAME_LENGTH].strip(ALLOWED_MARKS)
    if not word:
        return ""
    return word[0].upper() + word[1:]


def address(text, name):
    """Put the name in front of a sentence: 'You wake up.' -> 'Mika, you wake up.'
    The first letter becomes small, except for the word Sky (a name). No name: no change."""
    if not name or not text:
        return text
    if text.split()[0].strip(",.!?'s") != "Sky":
        text = text[0].lower() + text[1:]
    return f"{name}, {text}"
