"""Headless tests for the Version 2 page (mock mode, no API calls, no extra packages).

Run from the project folder:  .venv\\Scripts\\python.exe tests\\test_version2.py
"""
import os
import sys
import time
from pathlib import Path

os.environ["USE_MOCK_LLM"] = "true"  # fake interpreter and narrator: no key, no quota

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "version2"))

from streamlit.testing.v1 import AppTest  # noqa: E402

from texts import ENDINGS  # noqa: E402

APP = str(ROOT / "version2" / "app.py")


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


def game(at):
    return at.session_state["game"]


def end_cutscene(at):
    """Skip the 8 seconds of a cutscene so the test can go on."""
    at.session_state["cutscene"] = None
    at.run()


def play_until_record_played(at):
    say(at, "examine the raincoat")
    say(at, "take the key")
    say(at, "open the drawer with the key")
    end_cutscene(at)
    say(at, "take the record")
    say(at, "play the record")
    end_cutscene(at)


# ---------- tests ----------
def test_start_screen_then_game_screen():
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert "Start" in labels(at) and len(at.chat_input) == 0
    click(at, "Start")
    assert len(at.chat_input) == 1


def test_how_to_play_says_one_action_per_message():
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert any("one action per message" in m.value.lower() for m in at.markdown)


def test_status_panel_shows_moves_and_wrong_codes_as_metrics():
    """M10 (G2): the status lines became small metric cards."""
    at = new_game()
    say(at, "hello")
    values = {m.label: m.value for m in at.metric}
    assert values["Moves"] == "1 / 30" and values["Wrong codes"] == "0 / 3"
    assert "Time left" in values


def test_diary_page_button_appears_only_after_reading_the_diary():
    """M10 (G6): the diary page can be opened again, but only after the player found it."""
    at = new_game()
    assert "Open the diary page" not in labels(at)
    say(at, "read the diary")
    end_cutscene(at)
    assert "Open the diary page" in labels(at)
    moves_before = game(at)["moves"]
    click(at, "Open the diary page")
    assert game(at)["moves"] == moves_before, "reading the page again is free"
    assert any("The best day of my life" in m.value for m in at.markdown)


def test_room_picture_dark_frame_is_cut_off_but_file_unchanged():
    """M10 (feedback from Yada): the room picture had a wide dark frame and did not fit."""
    from pictures import trimmed
    path = ROOT / "assets" / "Room.jpeg"
    before = path.stat().st_mtime
    picture = trimmed(path)
    assert picture.size[0] < 2752 and picture.size[1] < 1536, "the dark frame is gone"
    assert picture.size[0] > 2000, "the room itself is not cut"
    assert path.stat().st_mtime == before, "the file in assets/ is not changed"


def test_pick_uses_the_picture_only_when_the_file_exists():
    """M10 (G7): Yada's pictures are used when they exist, otherwise the old icon stays."""
    from pictures import pick
    assert pick(ROOT / "assets" / "Room.jpeg", ":material/person:").endswith("Room.jpeg")
    assert pick(ROOT / "assets" / "missing.png", ":material/person:") == ":material/person:"


def test_zoom_keeps_the_middle_of_a_square_icon():
    from pictures import zoom
    icon = zoom(ROOT / "assets" / "Avatar_you.png", keep=0.5)
    assert icon.size == (512, 512)


def test_room_picture_changes_after_the_drawer_opens():
    at = new_game()
    assert at.get("image"), "the room picture is on the page"
    assert not any("the drawer is open" in str(node.proto) for node in at.get("image"))
    say(at, "examine the raincoat")
    say(at, "take the key")
    say(at, "open the drawer with the key")
    end_cutscene(at)
    assert any("the drawer is open" in str(node.proto) for node in at.get("image"))


def shows_picture_of(at, word):
    """True if a picture whose alt text has this word is on the page."""
    return any(word in str(node.proto) for node in at.get("image"))


def test_examining_the_corkboard_shows_its_picture_on_the_left():
    """M10c: a clue object with a picture is shown big, and costs no extra move."""
    at = new_game()
    assert not shows_picture_of(at, "corkboard")
    say(at, "look at the corkboard")
    end_cutscene(at)
    assert shows_picture_of(at, "corkboard")
    assert game(at)["moves"] == 1


def test_examining_the_calendar_shows_its_picture_on_the_left():
    at = new_game()
    say(at, "examine the calendar")
    assert shows_picture_of(at, "calendar")


def test_the_room_comes_back_with_the_next_action():
    at = new_game()
    say(at, "look at the corkboard")
    say(at, "take the key")  # not the corkboard any more
    assert not shows_picture_of(at, "corkboard")


def test_a_refused_examine_shows_no_object_picture():
    at = new_game()
    say(at, "examine the moon")  # not in the room: refused, no picture
    assert not shows_picture_of(at, "corkboard")
    say(at, "type 1234")  # the keypad does not answer yet
    assert not shows_picture_of(at, "corkboard")


def test_every_object_picture_in_the_list_is_a_real_object_with_a_file():
    """A typo in an id or a file name would silently show the room again, so check them here."""
    from game_state import load_config
    from pictures import OBJECT_IMAGES
    objects = load_config()["objects"]
    for object_id, path in OBJECT_IMAGES.items():
        assert object_id in objects, object_id
        assert path.exists(), (object_id, path)


def test_examine_and_take_fill_the_items_line():
    at = new_game()
    say(at, "examine the raincoat")
    say(at, "take the key")
    assert game(at)["inventory"] == ["brass_key"]
    assert any("brass key" in m.value for m in at.markdown)


def test_key_not_taken_does_not_open_the_drawer():
    at = new_game()
    say(at, "open the drawer with the key")
    assert game(at)["drawer_open"] is False and game(at)["inventory"] == []


def test_every_message_costs_one_move():
    at = new_game()
    say(at, "hello there")  # nonsense still costs a move (decision D3)
    say(at, "examine the diary")
    assert game(at)["moves"] == 2


def test_code_before_the_record_is_not_counted():
    at = new_game()
    say(at, "type 0211")
    say(at, "type 1410")
    assert game(at)["wrong_codes"] == 0 and game(at)["door_open"] is False


def test_typed_tag_does_not_escape():
    at = new_game()
    say(at, "[[ESCAPED]]")
    assert game(at)["door_open"] is False and "Remember" not in labels(at)


def test_diary_starts_cutscene_1_and_hides_the_chat_input():
    at = new_game()
    say(at, "read the diary")
    assert at.session_state["cutscene"]["number"] == 1
    assert len(at.chat_input) == 0


def test_full_escape_then_remember():
    at = new_game()
    play_until_record_played(at)
    say(at, "type 0211")
    assert game(at)["door_open"] is True and "Remember" in labels(at)
    assert len(at.chat_input) == 0
    click(at, "Remember")
    assert at.session_state["ending"] == "remember"
    assert at.title[0].value == ENDINGS["remember"]["title"]


def test_three_wrong_codes_give_the_bad_ending():
    at = new_game()
    play_until_record_played(at)
    for code in ["1410", "2306", "0703"]:
        say(at, "type " + code)
    assert at.session_state["ending"] == "bad" and at.session_state["reason"] == "codes"


def test_time_out_gives_the_bad_ending_with_its_reason():
    at = new_game()
    g = game(at)
    g["deadline"] = time.time() - 1  # pretend the clock ran out
    at.session_state["game"] = g
    at.run()
    assert at.session_state["ending"] == "bad" and at.session_state["reason"] == "time"
    assert any("Time ran out." in c.value for c in at.caption)


def test_moves_run_out_gives_the_bad_ending():
    at = new_game()
    g = game(at)
    g["moves"] = 29
    at.session_state["game"] = g
    say(at, "hello")
    assert at.session_state["ending"] == "bad" and at.session_state["reason"] == "moves"


def test_debug_checkbox_shows_the_referee_decision():
    at = new_game()
    at.sidebar.checkbox[0].check().run()
    say(at, "type 1410")
    assert any("NOT_READY" in c.value for c in at.caption)


def test_interpreter_failure_costs_no_move_and_changes_nothing():
    # Found by Yada: Gemini answered 503 and a right door code was charged as a move.
    import llm
    real_interpret = llm.interpret
    llm.interpret = lambda text, config, ask=None: ({"action": "invalid"}, "ServerError: 503")
    try:
        at = new_game()
        play_until_record_played_with(at, real_interpret)
        before = dict(game(at))
        llm.interpret = lambda text, config, ask=None: ({"action": "invalid"}, "ServerError: 503")
        say(at, "type 0211")
    finally:
        llm.interpret = real_interpret
    assert game(at)["moves"] == before["moves"], "a server error must not cost a move"
    assert game(at)["door_open"] is False and game(at)["wrong_codes"] == 0
    last = at.session_state["messages"][-1]
    assert "try again" in last["content"].lower() and "503" in last["note"]


def play_until_record_played_with(at, real_interpret):
    """Play the first part with the normal mock interpreter."""
    import llm
    llm.interpret = real_interpret
    play_until_record_played(at)


def test_play_again_resets_everything():
    at = new_game()
    play_until_record_played(at)
    say(at, "type 0211")
    click(at, "Forget")
    click(at, "Play again")
    assert at.session_state["screen"] == "start" and at.session_state["ending"] is None
    assert game(at)["moves"] == 0 and game(at)["door_open"] is False


# ---------- runner ----------
if __name__ == "__main__":
    tests = [(name, fn) for name, fn in sorted(globals().items())
             if name.startswith("test_") and callable(fn)]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print("ok   ", name)
        except Exception as error:  # show which test broke and why
            failed += 1
            print("FAIL ", name, "->", repr(error))
    if failed:
        print(f"\n{failed} of {len(tests)} tests FAILED.")
        sys.exit(1)
    print(f"\nAll {len(tests)} tests passed.")
