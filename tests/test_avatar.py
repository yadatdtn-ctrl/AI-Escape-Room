"""Tests for version2/avatar.py: where the avatar goes, which way it faces, and how it is drawn.
No Streamlit and no LLM here.

Run from the project folder:  .venv\\Scripts\\python.exe tests\\test_avatar.py
"""
import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "version2"))

from avatar import AVATAR_HEIGHT, AVATAR_SPOTS, facing, goal, place_avatar  # noqa: E402

with open(ROOT / "version2" / "game_config.json", encoding="utf-8") as file:
    CONFIG = json.load(file)
OBJECTS = CONFIG["objects"]


# ---------- where the avatar goes ----------
def test_examine_goes_to_the_object():
    assert goal({"action": "examine", "target": "bed"}, True, OBJECTS) == "bed"
    assert goal({"action": "examine", "target": "pillow"}, True, OBJECTS) == "bed"  # an alias


def test_use_goes_to_the_target_object():
    action = {"action": "use", "item": "brass_key", "target": "drawer"}
    assert goal(action, True, OBJECTS) == "drawer"


def test_enter_code_goes_to_the_door():
    action = {"action": "enter_code", "target": "keypad", "code": "1111"}
    assert goal(action, True, OBJECTS) == "door"


def test_refused_or_other_actions_stay():
    assert goal({"action": "examine", "target": "bed"}, False, OBJECTS) is None  # refused
    assert goal({"action": "look_around"}, True, OBJECTS) is None
    assert goal({"action": "take", "target": "brass_key"}, True, OBJECTS) is None
    assert goal({"action": "examine", "target": "moon"}, True, OBJECTS) is None  # unknown


def test_every_object_has_a_spot():
    assert set(OBJECTS) <= set(AVATAR_SPOTS)
    assert "start" in AVATAR_SPOTS
    for x, y in AVATAR_SPOTS.values():
        assert 0 <= x <= 100 and 0 <= y <= 100


def test_facing():
    assert facing("start", "door", "right") == "left"   # the door is on the left
    assert facing("door", "bed", "left") == "right"
    assert facing("desk", "desk", "left") == "left"     # same place: keep the way it looks


# ---------- drawing ----------
def feet(room, spot):
    """The pixel of the room picture where the avatar's feet stand."""
    x, y = AVATAR_SPOTS[spot]
    return int(room.width * x / 100), int(room.height * y / 100)


def test_place_avatar_paints_at_the_feet_and_keeps_the_room():
    room = Image.new("RGB", (200, 100), (0, 0, 0))
    sprite = Image.new("RGBA", (10, 20), (255, 0, 0, 255))
    picture = place_avatar(room, sprite, "bed", "right")
    x, y = feet(room, "bed")
    assert picture.getpixel((x, y - 3)) == (255, 0, 0)   # just above the feet: the avatar
    assert picture.getpixel((0, 0)) == (0, 0, 0)         # a far corner: still the room
    assert room.getpixel((x, y - 3)) == (0, 0, 0)        # the original picture is not changed
    assert AVATAR_HEIGHT > 0


def test_place_avatar_mirrors_for_left():
    room = Image.new("RGB", (200, 100), (0, 0, 0))
    sprite = Image.new("RGBA", (10, 20), (0, 0, 0, 0))   # transparent ...
    sprite.paste((255, 0, 0, 255), (5, 0, 10, 20))        # ... with only its right half red
    x, y = feet(room, "start")
    looking_right = place_avatar(room, sprite, "start", "right")
    looking_left = place_avatar(room, sprite, "start", "left")
    assert looking_right.getpixel((x + 2, y - 3)) == (255, 0, 0)
    assert looking_right.getpixel((x - 3, y - 3)) == (0, 0, 0)
    assert looking_left.getpixel((x - 3, y - 3)) == (255, 0, 0)
    assert looking_left.getpixel((x + 2, y - 3)) == (0, 0, 0)


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
