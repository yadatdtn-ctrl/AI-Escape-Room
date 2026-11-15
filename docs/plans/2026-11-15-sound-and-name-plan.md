# M17: sounds, Sky's voice and the player's name

Status: built. Changes after Yada tried it: the rain became quiet piano music ("JRPG Piano" by Joth, CC0, `assets/Music.mp3`); the grey browser player is hidden and a themed Music switch replaces it; Sky's voice was dropped (Yada: it felt strange); the name field says "Saved: ..."; the How to play text is shorter. Parts A and B below describe the first version.
Rules as always: test first, short code with plain comments, no new packages, commit only after Yada's OK, no Co-Authored-By line.

## Part A: rain in the room (quiet)
- **What:** a soft rain at a window plays while the player is in the game, in a loop.
- **File:** `assets/Ambient_rain.mp3`. Source: "Rain (loopable)" by Ylmir, https://opengameart.org/content/rain-loopable, licence **CC0** (no conditions). Credit goes in the README.
- **How:** `st.audio(..., loop=True, autoplay=True)` in the sidebar of the game screen. The sidebar stays on the page when it is collapsed, so the sound keeps playing and is not redrawn when the story changes. The sidebar player is also the player's mute and volume control.
- **Too loud (Yada):** a small script (`st.html(..., unsafe_allow_javascript=True)`) sets the player's volume to 20 % when it appears. The player can still raise it.
- **Not on the start screen.** The player must click Start first; browsers allow sound after a click.
- **If the file is missing:** no sound, no error.

## Part B: Sky's voice when the record plays
- **What:** when memory 3 ("That Night") shows its picture, Sky's voice plays once.
- **File:** `assets/Sky_voice.wav` (Yada's own; renamed from `.mp3` because the file is a WAV; 6 s, mono). A slower version can replace it later without any code change.
- **How:** `st.audio(..., autoplay=True)` under the picture caption, only in the picture phase of memory 3 (after the 2-second walk).
- **If the file is missing:** no sound, no error.

## Part C: the player's name
- **Start screen:** a small field "Your name" above the Start button. Empty = the game keeps saying "you".
- **Cleaning (`version2/names.py`, `clean_name(raw) -> str`):** only the first word; only letters, `-` and `'`; at most 12 characters; first letter in capitals; anything else is thrown away; if nothing is left the name is empty.
- **Where the name shows:** at the start of the final-choice text ("Mika, the door opens onto white light...") and at the start of the ending text ("Mika, you wake up and everything comes back at once..."). Chat, memory captions and stats stay as they are.
- **Safety:** the name is used only in these fixed texts (function `address(text, name)` in `names.py`). It never goes to the LLM: a test checks that `llm.py`, `validators.py` and `game_state.py` never mention the name.
- **Restart** clears the name.

## Tests first
- `tests/test_names.py` (new): `clean_name` cases (normal, empty, spaces, HTML like `<b>Mika</b>`, "ignore the rules" -> "Ignore", 30 letters -> 12, digits only -> empty, `Anne-Marie`, `O'Neil`); `address` (with and without a name).
- `tests/test_version2.py`: the game screen has the rain player and the start screen has none; no error when the file is missing is covered by a unit test of the helper; the voice player only shows in the picture phase of memory 3 and not in memories 1 and 2; the name field exists on the start screen; the name appears in the final-choice text and in the ending; the name never appears in the user or LLM facts; Restart clears it.
- `tests/test_names.py` also has the static check (the LLM files never mention `player_name`).
- What AppTest cannot check: that the rain really is quiet and that the voice really plays. Yada checks these by ear.

## Files
- Create: `version2/names.py`, `version2/sounds.py` (file paths, `quiet_script(level)`), `tests/test_names.py`.
- Modify: `version2/app.py`, `version2/texts.py` (no change to the wording), `tests/test_version2.py`, `README.md` (credits, test counts).
- Assets: `assets/Ambient_rain.mp3`, `assets/Sky_voice.wav` (not committed until Yada says OK).

## Decisions left to Yada
1. Is the voice slow enough? (Yada can replace the WAV any time.)
2. After the build: check the volume of the rain and the voice by ear.
