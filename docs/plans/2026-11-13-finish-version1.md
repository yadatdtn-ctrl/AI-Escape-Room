# Finish Version 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish Version 1 of the "Sky" escape room: commit the cutscenes (M4c), add the final choice (Remember / Forget) and the three ending screens (M4d), protect it with a small test file, and tag the result `v1`.

**Architecture:** Version 1 keeps the LLM in charge: Gemini writes the story and hidden tags, and `version1/app.py` (Streamlit) reacts to the tags. M4d adds one new state value use (`ending = "remember" | "forget" | "bad"`), a final-choice block with two buttons that appears when `escaped` is True, and ONE generic ending screen that reads its title and text from `version1/texts.py` and its picture from `assets/`. Tests use Streamlit's headless `AppTest` in mock mode, so they need no API key and no extra package.

**Tech Stack:** Python 3.14, Streamlit 1.67 (`st.fragment`, `st.columns`, `streamlit.testing.v1.AppTest`), google-genai (not called in tests), python-dotenv.

**Working rules for this project (from Yada):**
- Work milestone by milestone; after each milestone STOP and wait for Yada to write "NEXT".
- Before every commit: run `git status`, show it, show the message, and wait for Yada's OK. `.env` must never be staged.
- Never push or push tags without asking Yada.
- Texts marked `[PLACEHOLDER]` are intentional: Yada replaces them later. Do not "improve" them.
- Commit messages end with: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

**Not in this plan:** the "alive" ideas (walking avatar, clickable diary page). They get their own plan after Yada chooses option A, B or C.

---

## File structure

| File | Status | Responsibility |
|---|---|---|
| `version1/texts.py` | Modify | All player-facing story texts: cutscene captions, final-choice text, bad-ending reasons, the three endings (`ENDINGS` dict). Placeholders. |
| `version1/app.py` | Modify | Page flow: start screen → game screen → final choice → ending screen. |
| `tests/test_version1.py` | Create | Headless tests for Version 1 (mock mode). Runs with plain `python`, and later also with pytest if Yada approves installing it. |
| `version1/settings.py`, `version1/tags.py` | Already changed in M4c | No new changes; committed in Task 1. |

---

### Task 1: Commit M4c (cutscenes)

M4c is already written and was tested by Yada in the browser with real Gemini (screenshots of The Pier, The Rooftop and That Night with the paused clock).

**Files:**
- Commit: `version1/app.py`, `version1/settings.py`, `version1/tags.py`, `version1/texts.py`

- [ ] **Step 1: Show the status to Yada**

Run: `git status --short`
Expected:
```
 M version1/app.py
 M version1/settings.py
 M version1/tags.py
 M version1/texts.py
```

- [ ] **Step 2: Check the settings are the real values (not test values)**

Run: `grep -n "TIME_LIMIT_SECONDS\|CUTSCENE_SECONDS" version1/settings.py`
Expected: `TIME_LIMIT_SECONDS = 5 * 60` and `CUTSCENE_SECONDS = 8` (or a value Yada chose on purpose, e.g. 12). If `TIME_LIMIT_SECONDS` is a small test value like `20`, STOP and ask Yada to restore it.

- [ ] **Step 3: Wait for Yada's OK, then commit**

```bash
git add version1/app.py version1/settings.py version1/tags.py version1/texts.py
git commit -F - <<'EOF'
M4c: cutscenes with paused clock and time refund

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```
Expected: one new commit; `git status --short` prints nothing.

---

### Task 2: Write the failing tests for the final choice and endings

**Files:**
- Create: `tests/test_version1.py`

- [ ] **Step 1: Create the test file**

```python
"""Headless tests for Version 1 (mock mode, no API calls, no extra packages).

Run from the project folder:  .venv\\Scripts\\python.exe tests\\test_version1.py
"""
import os
import sys
import time
from pathlib import Path

os.environ["USE_MOCK_LLM"] = "true"  # fake Game Master: no key, no quota

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "version1"))

from streamlit.testing.v1 import AppTest  # noqa: E402

from tags import parse_tags  # noqa: E402
from texts import ENDINGS  # noqa: E402

APP = str(ROOT / "version1" / "app.py")


# ---------- helpers ----------
def new_game():
    """Open the app and press Start."""
    at = AppTest.from_file(APP, default_timeout=30).run()
    click(at, "Start")
    return at


def click(at, label):
    [b for b in at.button if b.label == label][0].click().run()


def say(at, text):
    at.chat_input[0].set_value(text).run()


def labels(at):
    return [b.label for b in at.button]


# ---------- regression tests (already working before M4d) ----------
def test_tags_are_cut_out_of_the_text():
    clean, tags = parse_tags("You take the key. [[ITEM:brass_key]]")
    assert clean == "You take the key."
    assert tags == [("ITEM", "brass_key")]


def test_three_wrong_codes_give_the_bad_ending():
    at = new_game()
    for code in ["1410", "2306", "0703"]:
        say(at, "type " + code)
    assert at.session_state.ending == "bad"
    assert at.session_state.reason == "codes"


# ---------- M4d: final choice ----------
def test_escape_shows_final_choice_and_hides_the_chat_input():
    at = new_game()
    say(at, "type 0211")
    assert at.session_state.escaped is True
    assert at.session_state.ending is None
    assert "Remember" in labels(at) and "Forget" in labels(at)
    assert len(at.chat_input) == 0, "the player must not type after the door opens"


def test_remember_button_shows_the_remember_ending():
    at = new_game()
    say(at, "type 0211")
    click(at, "Remember")
    assert at.session_state.ending == "remember"
    assert at.title[0].value == ENDINGS["remember"]["title"]
    assert "Play again" in labels(at)


def test_forget_button_shows_the_forget_ending():
    at = new_game()
    say(at, "type 0211")
    click(at, "Forget")
    assert at.session_state.ending == "forget"
    assert at.title[0].value == ENDINGS["forget"]["title"]


# ---------- M4d: bad ending uses the same ending screen ----------
def test_time_out_shows_the_bad_ending_with_its_reason():
    at = new_game()
    at.session_state["deadline"] = time.time() - 1  # pretend the clock ran out
    at.run()
    assert at.session_state.ending == "bad"
    assert at.title[0].value == ENDINGS["bad"]["title"]
    assert any("Time ran out." in c.value for c in at.caption)


def test_play_again_resets_everything():
    at = new_game()
    say(at, "type 0211")
    click(at, "Forget")
    click(at, "Play again")
    assert at.session_state.screen == "start"
    assert at.session_state.ending is None
    assert at.session_state.escaped is False
    assert at.session_state.moves == 0


if __name__ == "__main__":
    tests = [f for name, f in list(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print("PASS", test.__name__)
    print(f"All {len(tests)} tests passed.")
```

- [ ] **Step 2: Run the tests and see them fail**

Run: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe tests/test_version1.py`
(PowerShell: `$env:PYTHONIOENCODING="utf-8"; .venv\Scripts\python.exe tests\test_version1.py`)
Expected: FAIL at import with `ImportError: cannot import name 'ENDINGS' from 'texts'` (because `ENDINGS` does not exist yet).

---

### Task 3: Add the ending texts (placeholders)

**Files:**
- Modify: `version1/texts.py` (whole file)

- [ ] **Step 1: Replace `version1/texts.py` with this version**

The cutscene texts stay exactly the same; `BAD_ENDING_TITLE` and `BAD_ENDING_TEXT` move into the new `ENDINGS` dict; `FINAL_CHOICE_TEXT` is new.

```python
"""Texts the player reads: cutscene captions, the final choice and the endings.

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
```

- [ ] **Step 2: Run the tests**

Run: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe tests/test_version1.py`
Expected: still FAIL, now inside the app: `ImportError: cannot import name 'BAD_ENDING_TEXT' from 'texts'` shown as an app exception, or the first M4d test fails (`AssertionError` on `"Remember" in labels(at)`). This is expected: `app.py` is changed in Task 4.

---

### Task 4: Final choice and one generic ending screen in `app.py`

**Files:**
- Modify: `version1/app.py:15` (import), `:17-24` (pictures), `:54` (comment), `:121-130` (ending screen), `:155-156` (final choice), `:164-165` (chat input)

- [ ] **Step 1: Change the import (line 15)**

Replace:
```python
from texts import BAD_ENDING_TEXT, BAD_ENDING_TITLE, BAD_REASONS, CUTSCENES
```
with:
```python
from texts import BAD_REASONS, CUTSCENES, ENDINGS, FINAL_CHOICE_TEXT
```

- [ ] **Step 2: Replace the single bad picture with one picture per ending (lines 17-24)**

Replace:
```python
ASSETS = Path(__file__).parent.parent / "assets"
ROOM_IMAGE = ASSETS / "Room.jpeg"
BAD_IMAGE = ASSETS / "Bad.jpeg"
CUTSCENE_IMAGES = {
```
with:
```python
ASSETS = Path(__file__).parent.parent / "assets"
ROOM_IMAGE = ASSETS / "Room.jpeg"
ENDING_IMAGES = {
    "remember": ASSETS / "Remember.jpeg",
    "forget": ASSETS / "Forget.jpeg",
    "bad": ASSETS / "Bad.jpeg",
}
CUTSCENE_IMAGES = {
```

- [ ] **Step 3: Update the comment of `ending` in `reset_game()` (line 54)**

Replace:
```python
    st.session_state.ending = None     # None while playing, "bad" when the player loses
```
with:
```python
    st.session_state.ending = None     # None while playing; then "remember", "forget" or "bad"
```

- [ ] **Step 4: Replace the bad-ending screen with one ending screen for all three (lines 121-130)**

Replace:
```python
# ---------- Bad ending screen ----------
if st.session_state.ending == "bad":
    st.title(BAD_ENDING_TITLE)
    st.image(str(BAD_IMAGE), width="stretch")
    st.caption(BAD_REASONS[st.session_state.reason])
    st.write(BAD_ENDING_TEXT)
    if st.button("Play again", type="primary"):
        reset_game()
        st.rerun()
    st.stop()
```
with:
```python
# ---------- Ending screen (remember, forget or bad) ----------
if st.session_state.ending:
    ending = ENDINGS[st.session_state.ending]
    st.title(ending["title"])
    st.image(str(ENDING_IMAGES[st.session_state.ending]), width="stretch")
    if st.session_state.ending == "bad":
        st.caption(BAD_REASONS[st.session_state.reason])
    st.write(ending["text"])
    if st.button("Play again", type="primary"):
        reset_game()
        st.rerun()
    st.stop()
```

- [ ] **Step 5: Replace the temporary green message with the final choice (lines 155-156)**

Replace:
```python
    if st.session_state.escaped:
        st.success("The door opens onto white light. (The final choice comes in M4d.)")
```
with:
```python
    if st.session_state.escaped and not scene:
        # The door is open: the player decides how the story ends
        st.write(FINAL_CHOICE_TEXT)
        remember_col, forget_col = st.columns(2)
        if remember_col.button("Remember", type="primary", width="stretch"):
            st.session_state.ending = "remember"
            st.rerun()
        if forget_col.button("Forget", width="stretch"):
            st.session_state.ending = "forget"
            st.rerun()
```

- [ ] **Step 6: Hide the chat input after the door opens (lines 164-165)**

Replace:
```python
    # No typing while a memory is playing
    player_text = None if scene else st.chat_input("Type what you do...")
```
with:
```python
    # No typing while a memory is playing, or after the door is open
    no_typing = scene or st.session_state.escaped
    player_text = None if no_typing else st.chat_input("Type what you do...")
```

- [ ] **Step 7: Run the tests and see them pass**

Run: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe tests/test_version1.py`
Expected:
```
PASS test_tags_are_cut_out_of_the_text
PASS test_three_wrong_codes_give_the_bad_ending
PASS test_escape_shows_final_choice_and_hides_the_chat_input
PASS test_remember_button_shows_the_remember_ending
PASS test_forget_button_shows_the_forget_ending
PASS test_time_out_shows_the_bad_ending_with_its_reason
PASS test_play_again_resets_everything
All 7 tests passed.
```
If a test fails, read the assertion message, fix `app.py`, and run again. Do not change a test to make it pass unless the test itself is wrong; explain to Yada if so.

- [ ] **Step 8: Check for Streamlit warnings**

Run the app headless once and look at the console for deprecation warnings (for example about `width`):
`.venv/Scripts/streamlit.exe run version1/app.py --server.headless=true --server.port=8765` (stop it with Ctrl+C after it prints the URL and you have loaded it once).
Expected: no `DeprecationWarning` and no traceback in the console.

---

### Task 5: Yada's browser test (real Gemini)

**Files:** none (manual test).

- [ ] **Step 1: Yada plays the full game once with real Gemini**

`.env`: `USE_MOCK_LLM=false`. Run `streamlit run version1/app.py`, press Start, and play: `examine the raincoat` → `read the diary` → `open the drawer with the key` → `play the record` → `type 0211 on the keypad`.
Expected: three cutscenes; after 0211 the chat input disappears and the text + **Remember** / **Forget** buttons appear under the status lines.

- [ ] **Step 2: Yada checks both endings**

Click **Remember** → Remember title, `Remember.jpeg` picture, placeholder text, **Play again**. Play again, escape again, click **Forget** → `Forget.jpeg`.
Expected: both screens show; **Play again** returns to the start screen.

- [ ] **Step 3: Yada sends screenshots** of the final choice and of one ending. Note anything that looks wrong; do not fix V1 "weaknesses" in Gemini's behaviour (they are evidence for M5).

---

### Task 6: Commit M4d

**Files:**
- Commit: `version1/app.py`, `version1/texts.py`, `tests/test_version1.py`, `docs/plans/2026-11-13-finish-version1.md`

- [ ] **Step 1: Show the status to Yada**

Run: `git status --short`
Expected:
```
 M version1/app.py
 M version1/texts.py
?? docs/plans/
?? tests/
```
Check that `.env` is NOT in the list.

- [ ] **Step 2: Wait for Yada's OK, then commit**

```bash
git add version1/app.py version1/texts.py tests/test_version1.py docs/plans/2026-11-13-finish-version1.md
git commit -F - <<'EOF'
M4d: final choice (Remember / Forget), three ending screens, Version 1 tests

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
```
Expected: one new commit; `git status --short` prints nothing.

---

### Task 7: Tag Version 1 and (only with OK) push

**Files:** none (git tag).

- [ ] **Step 1: Run the tests one last time on the committed code**

Run: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe tests/test_version1.py`
Expected: `All 7 tests passed.`

- [ ] **Step 2: Create the tag**

```bash
git tag -a v1 -m "Version 1: the LLM is the Game Master (hidden tags, no validation)"
git tag -n
```
Expected: `v1   Version 1: the LLM is the Game Master (hidden tags, no validation)`

- [ ] **Step 3: Ask Yada before pushing**

Show `git log --oneline origin/main..main` (the commits GitHub does not have yet) and ask: "Push these commits and the tag `v1` to the private repository?"
Only after OK:
```bash
gh auth status   # must show yadatdtn-ctrl as the active account
git push origin main
git push origin v1
```
Expected: `main -> main` and `* [new tag] v1 -> v1`.

- [ ] **Step 4: STOP**

Milestone M4 is done. Tell Yada what was tested (headless tests + Yada's browser test) and what was not, then wait for "NEXT" (M5: Version 1 testing with the 5 challenges).
