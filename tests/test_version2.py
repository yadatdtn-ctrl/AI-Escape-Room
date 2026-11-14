"""Headless tests for the Version 2 page (mock mode, no API calls, no extra packages).

Run from the project folder:  .venv\\Scripts\\python.exe tests\\test_version2.py
"""
import os
import sys
import time
from pathlib import Path

os.environ["USE_MOCK_LLM"] = "true"  # fake interpreter and narrator: no key, no quota
os.environ["SKY_NO_TYPEWRITER"] = "true"  # the story appears at once, so the tests stay fast

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


def test_start_button_is_under_the_picture_so_it_is_always_visible():
    """Yada's screen: the button was lowest on the page, behind the long instructions."""
    at = AppTest.from_file(APP, default_timeout=30).run()
    image_nodes = [n for n in at.get("image")]
    assert image_nodes and "Start" in labels(at)
    # In the page tree, the first column holds the picture and the Start button; the second the text.
    first_column = at.columns[0]
    assert any(b.label == "Start" for b in first_column.button), "Start is in the picture's column"


def test_how_to_play_says_one_action_per_message():
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert any("one action per message" in m.value.lower() for m in at.markdown)


def test_how_to_play_suggests_a_first_step():
    """M11 (Yada said yes): a gentle start that gives nothing away."""
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert any("start by looking around" in m.value.lower() for m in at.markdown)


def test_how_to_play_does_not_give_away_the_solution():
    """M11 (idea from Yada): the examples must teach the sentence form, not the puzzle path."""
    at = AppTest.from_file(APP, default_timeout=30).run()
    text = " ".join(m.value.lower() for m in at.markdown if "one action per message" in m.value.lower())
    assert text, "the How to play text is on the page"
    for spoiler in ["raincoat", "brass", "take the key", "drawer", "diary", "record", "corkboard"]:
        assert spoiler not in text, spoiler


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


def test_bed_desk_record_player_and_window_show_their_pictures():
    """M11: the four new close-ups."""
    for sentence, word in [("examine the bed", "bed"), ("examine the desk", "desk"),
                           ("examine the record player", "record player"),
                           ("look out of the window", "window")]:
        at = new_game()
        say(at, sentence)
        assert shows_picture_of(at, word), sentence


def test_a_close_up_has_a_button_back_to_the_room_that_costs_nothing():
    """Yada: after the corkboard there was no way back to the room except typing."""
    for sentence, word in [("look at the corkboard", "corkboard"), ("look at the bed", "bed"),
                           ("examine the calendar", "calendar"), ("look out of the window", "window")]:
        at = new_game()
        assert "Back to the room" not in labels(at)
        say(at, sentence)
        assert shows_picture_of(at, word) and "Back to the room" in labels(at), sentence
        moves = game(at)["moves"]
        click(at, "Back to the room")
        assert not shows_picture_of(at, word) and "Back to the room" not in labels(at), sentence
        assert game(at)["moves"] == moves, "going back is free"


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


# ---------- M12 task 5: ending stats ----------
def stats_on_screen(at):
    return {m.label: m.value for m in at.metric}


def test_ending_shows_the_run():
    at = new_game()
    play_until_record_played(at)  # 5 moves, 2 memories (the drawer and the record)
    say(at, "type 0211")
    click(at, "Remember")
    shown = stats_on_screen(at)
    assert shown["Moves"] == "6 / 30" and shown["Wrong codes"] == "0 / 3"
    assert shown["Memories found"] == "2 / 3"
    assert "Time used" in shown


def test_the_stats_do_not_change_after_the_ending_started():
    at = new_game()
    play_until_record_played(at)
    say(at, "type 0211")
    click(at, "Forget")
    first = stats_on_screen(at)["Time used"]
    time.sleep(1.2)
    at.run()
    assert stats_on_screen(at)["Time used"] == first


def test_time_out_shows_the_full_time_used_never_more():
    """Review focus 4."""
    at = new_game()
    g = game(at)
    g["deadline"] = time.time() - 1  # the clock ran out a second ago
    at.session_state["game"] = g
    at.run()
    assert stats_on_screen(at)["Time used"] == "5:00"


def test_play_again_clears_the_stats_and_locks_the_memories_again():
    """Review focus 3."""
    at = new_game()
    play_until_record_played(at)
    say(at, "type 0211")
    click(at, "Forget")
    click(at, "Play again")
    assert at.session_state["stats"] is None
    click(at, "Start")
    assert locked_cards(at) == 3


# ---------- M12 task 4: item cards ----------
def test_empty_backpack_says_so():
    at = new_game()
    assert any("No items yet" in c.value for c in at.caption)


def test_item_card_shows_an_icon_and_the_name_when_there_is_no_picture():
    at = new_game()
    say(at, "examine the raincoat")
    say(at, "take the key")
    assert any(":material/key:" in m.value and "brass key" in m.value for m in at.markdown)
    assert not any("No items yet" in c.value for c in at.caption)


def test_every_item_picture_in_the_list_is_a_real_item():
    from game_state import load_config
    from pictures import ITEM_IMAGES
    for item_id in ITEM_IMAGES:
        assert item_id in load_config()["items"], item_id


# ---------- M12 task 3: typewriter story ----------
def with_typewriter(play):
    """Run play() with the typewriter switched on, then switch it off again."""
    os.environ["SKY_NO_TYPEWRITER"] = "false"
    try:
        return play()
    finally:
        os.environ["SKY_NO_TYPEWRITER"] = "true"


def test_newest_story_is_marked_as_shown_before_it_is_typed():
    """Review focus 1: if the player sends the next message while the text is typing,
    the story must not be lost, so it is marked as shown first."""
    at = new_game()
    say(at, "examine the raincoat")
    assert at.session_state["messages"][-1].get("fresh") is False
    assert any("brass key" in m.value for m in at.markdown)


def test_typing_time_is_given_back_to_the_clock():
    def play():
        at = new_game()
        before = game(at)["deadline"]
        say(at, "examine the bed")  # about 30 words, no memory starts
        return game(at)["deadline"] - before

    assert with_typewriter(play) > 0.5, "the typing seconds are added back"


def test_typing_time_is_not_given_back_twice_during_a_memory():
    """Review focus 2: the clock is already paused for the memory (8 s)."""
    def play():
        at = new_game()
        before = game(at)["deadline"]
        say(at, "read the diary")  # a memory starts
        return game(at)["deadline"] - before

    assert with_typewriter(play) < 8 + 0.5


# ---------- M12 task 2: game HUD ----------
def test_hud_shows_bars_for_time_and_moves():
    """The numbers stay in the metric cards; each has a thin bar under it (no second text line,
    so the panel is short enough for a laptop and a phone)."""
    at = new_game()
    say(at, "hello")
    bars = [node.proto.value for node in at.get("progress")]
    assert len(bars) == 2, bars          # one for the time, one for the moves
    assert 3 in bars, bars               # the moves bar: 1 of 30 moves is 3 percent
    assert all(not node.proto.text for node in at.get("progress")), "no repeated number in the bar"


def test_wrong_codes_are_shown_as_lock_icons_under_the_number():
    """A normal lock for a try left, a crossed-out lock for a try used. The words are the
    metric card right above ("Wrong codes 0 / 3"), so the icons need no text of their own."""
    at = new_game()
    assert any(m.value.strip() == ":material/lock: " * 2 + ":material/lock:" for m in at.markdown)
    play_until_record_played(at)
    say(at, "type 1410")
    assert any(m.value.strip() == ":material/lock: :material/lock: :material/no_encryption:"
               for m in at.markdown)
    assert {m.label: m.value for m in at.metric}["Wrong codes"] == "1 / 3"


# ---------- M12 task 1: memory cards ----------
REPLAY_ICON = ":material/replay:"  # the replay button shows only an icon, so it fits any card width


def locked_cards(at):
    return sum("A locked memory" in str(node.proto) for node in at.get("image"))


def test_the_three_memory_cards_are_three_columns_of_one_row():
    """Yada's screen: the third card wrapped below the screen edge. Columns cannot wrap."""
    at = new_game()
    # the page has 2 big columns (picture | chat) and now 3 more for the memory cards
    assert len(at.columns) == 5, len(at.columns)


def test_memory_cards_are_locked_at_the_start():
    at = new_game()
    assert locked_cards(at) == 3
    assert not any(b.label == REPLAY_ICON for b in at.button)


def test_a_played_memory_unlocks_its_card_and_can_be_seen_again_for_free():
    at = new_game()
    say(at, "read the diary")  # plays memory 1
    end_cutscene(at)
    assert locked_cards(at) == 2
    assert [b.label for b in at.button].count(REPLAY_ICON) == 1, "one icon button, for the found memory"
    assert any("The Pier" in c.value for c in at.caption), "the title is a caption on the card"
    moves = game(at)["moves"]
    at.button(key="memory_1").click().run()
    assert game(at)["moves"] == moves, "opening a memory costs no move"


def test_locked_card_is_a_small_dark_placeholder_with_no_memory_in_it():
    """Yada: not a blurred preview, only dark grey with a ? so nothing of the memory shows."""
    from pictures import locked_card
    card = locked_card()
    assert card.size[0] * 9 == card.size[1] * 16, "same 16:9 shape as the memory pictures"
    assert card.size[0] <= 400, "small"
    assert max(max(pixel) for pixel in card.convert("RGB").getdata()) < 160, "dark, no bright parts"
    assert len(set(card.convert("RGB").getdata())) <= 3, "flat colors only: background, ?, nothing else"


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
