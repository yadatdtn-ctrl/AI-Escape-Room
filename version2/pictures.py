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


def pick(path, fallback):
    """Use the picture file if it exists, otherwise the fallback (for example a Material icon)."""
    return str(path) if Path(path).exists() else fallback


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
