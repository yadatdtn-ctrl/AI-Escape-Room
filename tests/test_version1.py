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


def test_ending_screen_puts_picture_and_text_side_by_side():
    # Bug found by Yada: a full-width picture is taller than the screen,
    # so the text and "Play again" were hidden below it.
    at = new_game()
    say(at, "type 0211")
    click(at, "Remember")
    assert len(at.columns) == 2, "picture left, text right"
    text_side = at.columns[1]
    assert text_side.title[0].value == ENDINGS["remember"]["title"]
    assert "Play again" in [b.label for b in text_side.button]


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
