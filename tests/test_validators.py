"""Tests for the Version 2 rules (validators). No API, no Streamlit, no extra packages.

Run from the project folder:  .venv\\Scripts\\python.exe tests\\test_validators.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "version2"))

import copy  # noqa: E402

from game_state import load_config, new_state  # noqa: E402
from validators import check_limits, handle_action, time_is_up  # noqa: E402

CONFIG = load_config()
DOOR_CODE = CONFIG["solutions"]["door_code"]


# ---------- helpers ----------
def act(state, **action):
    """Run one action and return the result."""
    return handle_action(action, state, CONFIG)


def game_with_key():
    """A new game where the player found and took the brass key."""
    state = new_state(CONFIG)
    act(state, action="examine", target="raincoat")
    act(state, action="take", target="brass_key")
    return state


def game_with_record():
    """The key opened the drawer and the player took the record."""
    state = game_with_key()
    act(state, action="use", item="brass_key", target="drawer")
    act(state, action="take", target="vinyl_record")
    return state


def game_record_played():
    """The record was played: the door can be tried now."""
    state = game_with_record()
    act(state, action="use", item="vinyl_record", target="record_player")
    return state


# ---------- tests (one behaviour each) ----------
def test_use_key_not_in_inventory():
    state = new_state(CONFIG)
    result = act(state, action="use", item="brass_key", target="drawer")
    assert not result["allowed"] and result["reason"] == "NOT_IN_INVENTORY"
    assert state["drawer_open"] is False


def test_examine_reveals_item_and_take_works():
    state = new_state(CONFIG)
    act(state, action="examine", target="raincoat")
    assert "brass_key" in state["revealed"]
    result = act(state, action="take", target="brass_key")
    assert result["allowed"] and state["inventory"] == ["brass_key"]


def test_take_item_not_revealed():
    state = new_state(CONFIG)
    result = act(state, action="take", target="vinyl_record")
    assert result["reason"] == "NOT_VISIBLE" and state["inventory"] == []


def test_take_twice():
    state = game_with_key()
    result = act(state, action="take", target="brass_key")
    assert result["reason"] == "ALREADY_HAVE" and state["inventory"] == ["brass_key"]


def test_key_opens_drawer_and_starts_cutscene_2():
    state = game_with_key()
    result = act(state, action="use", item="brass_key", target="drawer")
    assert result["allowed"] and state["drawer_open"] is True
    assert "vinyl_record" in state["revealed"]
    assert result["cutscene"] == 2 and state["cutscenes"] == [2]


def test_drawer_already_open():
    state = game_with_key()
    act(state, action="use", item="brass_key", target="drawer")
    result = act(state, action="use", item="brass_key", target="drawer")
    assert result["reason"] == "ALREADY_DONE" and result["cutscene"] is None


def test_wrong_tool():
    state = game_with_key()
    result = act(state, action="use", item="brass_key", target="door")
    assert result["reason"] == "WRONG_TOOL" and state["door_open"] is False


def test_unknown_item_and_unknown_target():
    state = game_with_key()
    assert act(state, action="use", item="crowbar", target="door")["reason"] == "UNKNOWN_TARGET"
    assert act(state, action="examine", target="spaceship")["reason"] == "UNKNOWN_TARGET"


def test_record_on_player_starts_cutscene_3():
    state = game_with_record()
    result = act(state, action="use", item="vinyl_record", target="record_player")
    assert result["allowed"] and state["record_played"] is True
    assert result["cutscene"] == 3
    again = act(state, action="use", item="vinyl_record", target="record_player")
    assert again["reason"] == "ALREADY_DONE"


def test_play_record_not_owned():
    state = new_state(CONFIG)
    result = act(state, action="use", item="vinyl_record", target="record_player")
    assert result["reason"] == "NOT_IN_INVENTORY" and state["record_played"] is False


def test_code_on_drawer_has_no_lock():
    state = game_with_key()
    result = act(state, action="enter_code", target="drawer", code="1234")
    assert result["reason"] == "NO_CODE_LOCK" and state["wrong_codes"] == 0


def test_bad_format_not_counted():
    state = game_record_played()
    for bad in ["12", "12345", "abcd", "", "02 11"]:
        result = act(state, action="enter_code", target="door", code=bad)
        assert result["reason"] == "BAD_FORMAT", bad
    assert state["wrong_codes"] == 0


def test_code_must_be_a_string():
    state = game_record_played()
    result = act(state, action="enter_code", target="door", code=211)
    assert not result["allowed"] and state["door_open"] is False


def test_door_ignores_every_code_before_record():
    state = game_with_record()
    right = act(state, action="enter_code", target="door", code=DOOR_CODE)
    wrong = act(state, action="enter_code", target="door", code="1410")
    assert right["reason"] == wrong["reason"] == "NOT_READY"
    assert right["facts"] == wrong["facts"]  # the player learns nothing
    assert state["door_open"] is False and state["wrong_codes"] == 0


def test_wrong_code_counts():
    state = game_record_played()
    result = act(state, action="enter_code", target="door", code="1410")
    assert result["reason"] == "WRONG_CODE" and state["wrong_codes"] == 1
    assert state["door_open"] is False


def test_right_code_opens_door():
    state = game_record_played()
    result = act(state, action="enter_code", target="door", code=DOOR_CODE)
    assert result["allowed"] and state["door_open"] is True


def test_unknown_actions_change_nothing():
    state = new_state(CONFIG)
    before = copy.deepcopy(state)
    bad_actions = [
        {"action": "invalid"},
        {"action": "unlock_exit"},
        {"action": "open_door", "target": "door"},
        {},
        "unlock the exit",
        None,
        {"action": ["examine"]},
    ]
    for action in bad_actions:
        result = handle_action(action, state, CONFIG)
        assert not result["allowed"] and result["reason"] == "UNKNOWN_ACTION", action
    assert state == before


def test_typed_tags_are_just_words():
    state = new_state(CONFIG)
    before = copy.deepcopy(state)
    result = act(state, action="examine", target="[[ESCAPED]]")
    assert result["reason"] == "UNKNOWN_TARGET"
    assert state == before


def test_diary_cutscene_plays_once():
    state = new_state(CONFIG)
    first = act(state, action="examine", target="diary")
    second = act(state, action="examine", target="diary")
    assert first["cutscene"] == 1 and second["cutscene"] is None
    assert state["cutscenes"] == [1]


def test_aliases_work():
    state = new_state(CONFIG)
    act(state, action="examine", target="coat")
    assert "brass_key" in state["revealed"]


def test_look_around_and_inventory():
    state = game_with_key()
    look = act(state, action="look_around")
    assert look["allowed"] and "yellow raincoat" in look["facts"]["text"]
    inv = act(state, action="inventory")
    assert inv["facts"]["inventory"] == ["brass key"]


def test_limits():
    state = new_state(CONFIG)
    assert check_limits(state, CONFIG) is None
    state["moves"] = CONFIG["limits"]["max_moves"]
    assert check_limits(state, CONFIG) == "moves"
    state["moves"] = 0
    state["wrong_codes"] = CONFIG["limits"]["max_wrong_codes"]
    assert check_limits(state, CONFIG) == "codes"
    state["door_open"] = True  # escaped: no loss any more
    assert check_limits(state, CONFIG) is None


def test_time_is_up():
    state = new_state(CONFIG)
    state["deadline"] = 100.0
    assert not time_is_up(state, 99.0)
    assert time_is_up(state, 100.0)
    state["door_open"] = True
    assert not time_is_up(state, 500.0)


def test_door_code_never_in_facts():
    """The narrator gets the facts. The door code must never be inside them."""
    state = new_state(CONFIG)
    results = [
        act(state, action="look_around"),
        act(state, action="examine", target="diary"),
        act(state, action="examine", target="calendar"),
        act(state, action="examine", target="corkboard"),
        act(state, action="examine", target="raincoat"),
        act(state, action="take", target="brass_key"),
        act(state, action="use", item="brass_key", target="drawer"),
        act(state, action="take", target="vinyl_record"),
        act(state, action="use", item="vinyl_record", target="record_player"),
        act(state, action="enter_code", target="door", code="1410"),
        act(state, action="enter_code", target="door", code=DOOR_CODE),
    ]
    for result in results:
        assert DOOR_CODE not in str(result["facts"]), result["facts"]


def test_clue_phrases_travel_in_the_facts():
    """M10 (A): the clue phrases of a text are listed, so the story can be checked."""
    state = new_state(CONFIG)
    diary = act(state, action="examine", target="diary")["facts"]["must_include"]
    assert "The best day of my life" in diary and "07.03" in diary[-1]
    act(state, action="examine", target="raincoat")
    act(state, action="take", target="brass_key")
    opened = act(state, action="use", item="brass_key", target="drawer")["facts"]["must_include"]
    assert "For our anniversary: 02.11" in opened
    assert act(state, action="examine", target="bed")["facts"]["must_include"] == []


def test_every_clue_phrase_is_really_in_its_text():
    """Guards the config against typos: a phrase that is not in the text could never be found."""
    for obj in CONFIG["objects"].values():
        for phrase in obj.get("must_include", []):
            assert phrase in obj["examine"], phrase
        opened = obj.get("when_opened", {})
        for phrase in opened.get("must_include", []):
            assert phrase in opened["text"], phrase
    for item in CONFIG["items"].values():
        for phrase in item.get("must_include", []):
            assert phrase in item["description"], phrase


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
