"""Version 2: the pixel avatar in the room. No Streamlit and no LLM in this file.

The avatar only moves after Python's referee has ALLOWED an action. It then stands in
front of the object the action was about. The LLM never sees where the avatar is.
"""
from PIL import Image, ImageOps

from validators import find_id

# Where the avatar's feet stand, in percent of the (trimmed) room picture: (x from the left, y from the top).
# "start" is the middle of the floor. The other keys are the object ids of game_config.json.
AVATAR_SPOTS = {
    "start": (50, 92),
    "door": (17, 92),
    "raincoat": (22, 90),
    "drawer": (30, 93),
    "diary": (34, 93),
    "desk": (38, 93),
    "window": (48, 86),
    "record_player": (55, 86),
    "corkboard": (66, 84),
    "calendar": (78, 84),
    "bed": (64, 93),
}

AVATAR_HEIGHT = 0.30  # the avatar is this part of the room picture's height


def goal(action, allowed, objects):
    """The spot the avatar walks to after this action, or None if it stays where it is."""
    if not allowed or not isinstance(action, dict):
        return None  # a refused action changes nothing, so the avatar does not move either
    name = action.get("action")
    if name == "enter_code":
        return "door"  # the keypad is on the door
    if name in ("examine", "use"):
        spot = find_id(action.get("target"), objects)
        return spot if spot in AVATAR_SPOTS else None
    return None  # look around, take, inventory: the avatar stays


def facing(old_spot, new_spot, current):
    """Look left when walking to the left, right when walking to the right."""
    old_x, new_x = AVATAR_SPOTS[old_spot][0], AVATAR_SPOTS[new_spot][0]
    if new_x < old_x:
        return "left"
    if new_x > old_x:
        return "right"
    return current  # same place: keep looking the same way


def place_avatar(room, sprite, spot, side):
    """A copy of the room picture with the avatar standing on 'spot'.
    The sprite faces right; for 'left' it is mirrored. The room picture itself is not changed."""
    height = max(1, int(room.height * AVATAR_HEIGHT))
    width = max(1, sprite.width * height // sprite.height)
    figure = sprite.convert("RGBA").resize((width, height), Image.NEAREST)  # NEAREST keeps pixels sharp
    if side == "left":
        figure = ImageOps.mirror(figure)
    x, y = AVATAR_SPOTS[spot]
    feet_x, feet_y = int(room.width * x / 100), int(room.height * y / 100)
    picture = room.convert("RGB")  # convert() makes a new picture, so the room stays as it was
    picture.paste(figure, (feet_x - width // 2, feet_y - height), figure)  # the sprite's own see-through parts
    return picture
