"""Version 2: small picture helper. No Streamlit and no LLM in this file.

The room picture has a wide dark frame around the drawing, so on the page it
looked like a box that did not fit. trimmed() cuts that frame off when the
picture is shown. The file in assets/ is never changed.
"""
from pathlib import Path

from PIL import Image  # Pillow is installed together with Streamlit


# Close-up pictures of clue objects (made by Yada). One line per picture: object id -> file.
# After a successful "examine" of one of these objects, the left side shows its picture.
OBJECT_IMAGES = {
    "corkboard": Path(__file__).parent.parent / "assets" / "Corkboard.png",
    "calendar": Path(__file__).parent.parent / "assets" / "Calendar.png",
    "bed": Path(__file__).parent.parent / "assets" / "Bed.png",
    "desk": Path(__file__).parent.parent / "assets" / "Desk.png",
    "record_player": Path(__file__).parent.parent / "assets" / "RecordPlayer.png",
    "window": Path(__file__).parent.parent / "assets" / "Window.png",
}


# Small pictures of the items (to be made by Yada). Until a file exists, the item card
# shows a Material icon instead.
ITEM_IMAGES = {
    "brass_key": Path(__file__).parent.parent / "assets" / "Item_brass_key.png",
    "vinyl_record": Path(__file__).parent.parent / "assets" / "Item_vinyl_record.png",
}


def pick(path, fallback):
    """Use the picture file if it exists, otherwise the fallback (for example a Material icon)."""
    return str(path) if Path(path).exists() else fallback


# A pixel "?" made of 5 x 7 squares (1 = a grey square)
QUESTION_MARK = ["01110", "10001", "00001", "00010", "00100", "00000", "00100"]


def locked_card(width=320):
    """The card of a memory the player has not found yet: flat dark grey with a pixel "?".
    Nothing of the real picture is in it, so nothing is given away. Same 16:9 shape as the memories."""
    height = width * 9 // 16
    card = Image.new("RGB", (width, height), (38, 42, 58))
    square = height // 9  # the size of one pixel of the "?"
    left = (width - 5 * square) // 2
    top = (height - 7 * square) // 2
    for row, line in enumerate(QUESTION_MARK):
        for column, mark in enumerate(line):
            if mark == "1":
                x, y = left + column * square, top + row * square
                card.paste((110, 116, 140), (x, y, x + square, y + square))
    return card


def zoom(path, keep=0.5):
    """Keep only the middle part of a square picture, so a small icon shows the figure bigger."""
    picture = Image.open(path).convert("RGB")
    width, height = picture.size
    cut_w, cut_h = int(width * (1 - keep) / 2), int(height * (1 - keep) / 2)
    return picture.crop((cut_w, cut_h, width - cut_w, height - cut_h))


def trimmed(path, darkness=35):
    """Return the picture without its dark frame (pixels darker than 'darkness' at the edges)."""
    picture = Image.open(path).convert("RGB")
    mask = picture.convert("L").point(lambda value: 255 if value > darkness else 0)
    box = mask.getbbox()  # the smallest box around everything that is not dark
    return picture.crop(box) if box else picture


def letterbox(picture, ratio, color=(14, 18, 32)):
    """Give the picture the shape 'ratio' (width / height) by adding bars in the page colour.
    Nothing of the picture is cut off. Used so a memory picture is as tall as the room picture."""
    picture = picture.convert("RGB")
    width, height = picture.size
    if abs(width / height - ratio) < 0.01:
        return picture  # already the right shape
    if width / height > ratio:  # too wide: bars above and below
        new_size = (width, round(width / ratio))
    else:  # too tall: bars left and right
        new_size = (round(height * ratio), height)
    canvas = Image.new("RGB", new_size, color)
    canvas.paste(picture, ((new_size[0] - width) // 2, (new_size[1] - height) // 2))
    return canvas


def fade_css(seconds, fade=1.5):
    """CSS for the memory picture: fade in, stay, fade out. It lasts as long as the cutscene."""
    start = round(fade / seconds * 100, 1)  # where the fade-in ends, in percent of the time
    end = round(100 - start, 1)             # where the fade-out begins
    return f"""<style>
.st-key-cutscene img {{ animation: scene {seconds}s linear forwards; }}
@keyframes scene {{
  0% {{ opacity: 0; }}
  {start}% {{ opacity: 1; }}
  {end}% {{ opacity: 1; }}
  100% {{ opacity: 0; }}
}}
</style>"""
