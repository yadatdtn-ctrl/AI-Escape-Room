"""Version 2: the Streamlit page. Python decides, the LLM only translates and describes.

Run from the project folder:  streamlit run version2/app.py
"""
import os
import time
from pathlib import Path

import streamlit as st
from PIL import Image

from game_state import count_move, load_config, new_state
from llm import interpret, narrate, use_mock
from avatar import facing, goal, place_avatar
from pictures import ITEM_IMAGES, OBJECT_IMAGES, fade_css, letterbox, locked_card, pick, trimmed, zoom
from texts import BAD_REASONS, CUTSCENES, ENDINGS, FINAL_CHOICE_TEXT, OPENING_TEXT, TRY_AGAIN_TEXT
from validators import check_limits, find_id, handle_action, time_is_up

CONFIG = load_config()  # the rulebook (only Python reads it)
LIMITS = CONFIG["limits"]

ASSETS = Path(__file__).parent.parent / "assets"
ROOM_IMAGE = ASSETS / "Room.jpeg"
ENDING_IMAGES = {
    "remember": ASSETS / "Remember.jpeg",
    "forget": ASSETS / "Forget.jpeg",
    "bad": ASSETS / "Bad.jpeg",
}
CUTSCENE_IMAGES = {
    1: ASSETS / "The Pier.jpeg",
    2: ASSETS / "The Rooftop.jpeg",
    3: ASSETS / "That Night.jpeg",
}
ROOM_OPEN_IMAGE = ASSETS / "Room_open.jpeg"  # the same room with the drawer open (by Yada)
DIARY_IMAGE = ASSETS / "Diary.jpeg"  # the diary page (by Yada)
SPRITE_IMAGE = ASSETS / "Sprite_you.png"  # the pixel avatar, facing right (by Yada); no file = no avatar
AVATAR_YOU = ASSETS / "Avatar_you.png"  # chat icon for the player (by Yada)
AVATAR_NARRATOR = ASSETS / "Avatar_narrator.png"  # chat icon for the narrator (by Yada)
ITEM_ICONS = {"brass_key": ":material/key:", "vinyl_record": ":material/album:"}  # until Yada's pictures
HUD_WIDTH = 150   # width in pixels of one block of the status panel (time, moves, wrong codes)
CHAT_HEIGHT = 400  # height in pixels of the chat box

INTRO = (
    "You will wake up in a room that is not yours. "
    "Somewhere in it is a way out. Look around, collect what you find, "
    "and listen to what the room remembers."
)

HOW_TO_PLAY = f"""
- Start by looking around.
- Type what you want to do in normal words, for example:
  *look around*, *examine the window*, *what am I carrying?*
  You can look at things, pick things up, use one thing on another, and type a code.
- Send **one action per message**: do one thing, then the next.
- You have **{LIMITS["time_seconds"] // 60} minutes** and **{LIMITS["max_moves"]} moves**.
  Every message you send is 1 move. The clock starts when you press Start.
- The door allows only **{LIMITS["max_wrong_codes"]} wrong codes**.
"""

# The sidebar starts closed: it is wide, and the game needs the room (Restart is still inside it).
st.set_page_config(page_title="Sky - Version 2", page_icon=":material/auto_stories:", layout="wide",
                   initial_sidebar_state="collapsed")


@st.cache_data
def room_picture(drawer_open=False):
    """The room picture without its dark frame (cut once, then kept in Streamlit's cache).
    After the drawer is opened, the picture with the open drawer is used, if it exists."""
    path = pick(ROOM_OPEN_IMAGE, str(ROOM_IMAGE)) if drawer_open else ROOM_IMAGE
    return trimmed(path)


@st.cache_data
def cutscene_picture(number):
    """A memory picture with bars added, so it is exactly as tall as the room picture (nothing below it jumps)."""
    room = room_picture()
    return letterbox(Image.open(CUTSCENE_IMAGES[number]), room.width / room.height)


@st.cache_data
def room_with_avatar(drawer_open, spot, side):
    """The room picture with the avatar standing on 'spot' (or without it, if the sprite file is missing)."""
    room = room_picture(drawer_open)
    if not SPRITE_IMAGE.exists():
        return room
    return place_avatar(room, Image.open(SPRITE_IMAGE), spot, side)


@st.cache_data
def avatars():
    """Yada's pixel icons, zoomed in so they are readable when small; Material icons if missing."""
    return {
        "user": zoom(AVATAR_YOU, keep=0.5) if AVATAR_YOU.exists() else ":material/person:",
        "assistant": zoom(AVATAR_NARRATOR, keep=0.8) if AVATAR_NARRATOR.exists()
        else ":material/auto_stories:",
    }


def reset_game():
    """Put the game back to the start (used at the beginning and by Restart)."""
    st.session_state.screen = "start"
    st.session_state.game = new_state(CONFIG)   # the rule state: only Python changes it
    st.session_state.game["deadline"] = None    # the moment the clock runs out (set at Start)
    st.session_state.messages = [{"role": "assistant", "content": OPENING_TEXT}]
    st.session_state.ending = None     # None while playing; then "remember", "forget" or "bad"
    st.session_state.reason = None     # why the player lost: "time", "moves" or "codes"
    st.session_state.cutscene = None   # the memory now: {"number": 1, "shows_at": time, "ends_at": time}
    st.session_state.viewing = None    # id of the object whose close-up picture is shown, or None
    st.session_state.close_up = None   # id of the object whose close-up can be opened now ("Look closer"), or None
    st.session_state.stats = None      # the numbers of the finished run (saved once, at the end)
    st.session_state.avatar = {"at": "start", "facing": "right"}  # where the pixel avatar stands


def save_stats():
    """Save the numbers of this run when the ending starts, so they do not change later.
    Time used = 5 minutes minus what was left (waiting for Gemini and typing time are not counted).
    If the door is open, the clock stopped at that moment."""
    if st.session_state.stats is not None:
        return
    stopped_at = game.get("door_opened_at") or time.time()
    seconds_left = max(0, game["deadline"] - stopped_at)
    st.session_state.stats = {
        "time_used": int(min(LIMITS["time_seconds"], LIMITS["time_seconds"] - seconds_left)),
        "moves": game["moves"],
        "wrong_codes": game["wrong_codes"],
        "memories": len(game["cutscenes"]),
    }


def lose(reason):
    """End the game with the bad ending."""
    save_stats()
    st.session_state.ending = "bad"
    st.session_state.reason = reason


def format_time(seconds):
    minutes, seconds = divmod(int(seconds), 60)
    return f"{minutes}:{seconds:02d}"


TYPE_DELAY = 0.03        # seconds between two words of the typewriter story
TYPE_MAX_SECONDS = 1.5   # a long story is typed faster, so it never takes longer than this
WALK_SECONDS = 2  # before a memory starts, the room with the avatar stays this long on screen


def typewriter_on():
    """The tests switch the typewriter off (SKY_NO_TYPEWRITER=true) so they stay fast."""
    return os.getenv("SKY_NO_TYPEWRITER", "false").lower() != "true"


def words(text, delay):
    """The text word by word, with a short pause after each word (for st.write_stream)."""
    for word in text.split(" "):
        yield word + " "
        time.sleep(delay)


def bar_value(part, whole):
    """A number between 0.0 and 1.0 for st.progress (never below 0 and never above 1)."""
    return max(0.0, min(1.0, part / whole))


def lock_icons(wrong, allowed):
    """One lock per try: a normal lock for a try left, a crossed-out lock for a try used.
    The metric card right above ("Wrong codes 0 / 3") already says it in words."""
    left = allowed - wrong
    return (":material/lock: " * left + ":material/no_encryption: " * wrong).strip()


def start_cutscene(number):
    """Play a memory and stop the clock: the player gets all the seconds back.
    First the room stays on screen for WALK_SECONDS, so the player sees the avatar at the object;
    then the memory picture is shown for the cutscene time."""
    seconds = LIMITS["cutscene_seconds"]
    shows_at = time.time() + WALK_SECONDS
    st.session_state.cutscene = {"number": number, "shows_at": shows_at, "ends_at": shows_at + seconds}
    st.session_state.game["deadline"] += WALK_SECONDS + seconds


@st.fragment(run_every=1)
def live_clock():
    """Shows the countdown. Streamlit re-runs ONLY this small part every second."""
    seconds_left = int(st.session_state.game["deadline"] - time.time())
    if seconds_left <= 0:
        lose("time")
        st.rerun()  # redraw the whole page so the bad ending appears
    st.metric("Time left", format_time(seconds_left))
    st.progress(bar_value(seconds_left, LIMITS["time_seconds"]))


@st.dialog("Sky's diary", width="medium")
def diary_page():
    """The diary page again. It shows the exact text from the config (all clues), and costs no move."""
    if DIARY_IMAGE.exists():
        st.image(str(DIARY_IMAGE), width="stretch", alt="A page of Sky's diary")
    st.markdown(CONFIG["objects"]["diary"]["examine"])


@st.dialog("A memory", width="large")
def memory_page(number):
    """A memory that was found before, shown again. It costs no move and no LLM call."""
    info = CUTSCENES[number]
    st.image(str(CUTSCENE_IMAGES[number]), width="stretch", alt=info["title"])
    st.write(f"**{info['title']}**: {info['caption']}")


@st.fragment(run_every=0.5)
def cutscene_watch():
    """Draws nothing. Checks twice a second if the memory picture should appear, or if the memory is over."""
    scene = st.session_state.cutscene
    if time.time() >= scene["ends_at"]:
        st.session_state.cutscene = None
        st.rerun()  # redraw the whole page: back to the room and the live clock
    elif time.time() >= scene["shows_at"] and not scene.get("shown"):
        scene["shown"] = True  # only once
        st.rerun()  # redraw the whole page: now the memory picture


# session_state = memory that Streamlit keeps while the page is open
if "screen" not in st.session_state:
    reset_game()
game = st.session_state.game  # short name for the rule state

# ---------- Sidebar: always visible ----------
with st.sidebar:
    st.header("Sky")
    with st.expander("How to play", expanded=False):
        st.markdown(HOW_TO_PLAY)
    if st.button("Restart"):
        reset_game()
        st.rerun()
    show_debug = st.checkbox("Show what the referee decided")
    if use_mock():
        st.caption("Mock mode: fake answers, no API calls.")

# ---------- Start screen ----------
if st.session_state.screen == "start":
    # Same shape as the game screen: picture on the left, words on the right
    picture_side, text_side = st.columns(2, vertical_alignment="center")
    with picture_side:
        st.image(room_picture(), width="stretch", alt="Sky's attic room at night")
        # The button sits under the picture, so it is always on screen, even when the
        # instructions on the right are long.
        if st.button("Start", type="primary", icon=":material/play_arrow:", width="stretch"):
            st.session_state.screen = "game"
            game["deadline"] = time.time() + LIMITS["time_seconds"]  # the clock starts NOW
            st.rerun()
    with text_side:
        st.title("Sky")
        st.write(INTRO)
        st.subheader("How to play")
        st.markdown(HOW_TO_PLAY)
    st.stop()

# ---------- Ending screen (remember, forget or bad) ----------
if st.session_state.ending:
    ending = ENDINGS[st.session_state.ending]
    # Side by side (like the game screen), so everything fits on one screen
    picture_side, text_side = st.columns(2, vertical_alignment="center")
    with picture_side:
        st.image(str(ENDING_IMAGES[st.session_state.ending]), width="stretch",
                 alt=ENDINGS[st.session_state.ending]["title"])
    with text_side:
        st.title(ending["title"])
        if st.session_state.ending == "bad":
            st.caption(BAD_REASONS[st.session_state.reason])
        st.write(ending["text"])
        run = st.session_state.stats
        if run:  # the run in numbers, like the end screen of a game
            with st.container(horizontal=True):
                st.metric("Time used", format_time(run["time_used"]))
                st.metric("Moves", f"{run['moves']} / {LIMITS['max_moves']}")
                st.metric("Wrong codes", f"{run['wrong_codes']} / {LIMITS['max_wrong_codes']}")
                st.metric("Memories found", f"{run['memories']} / {len(CUTSCENES)}")
        if st.button("Play again", type="primary"):
            reset_game()
            st.rerun()
    st.stop()

# ---------- Game screen: picture on the left, chat on the right ----------
left, right = st.columns(2)

with left:
    scene = st.session_state.cutscene  # a memory is on its way or playing: the clock is frozen
    if scene and time.time() >= scene["shows_at"]:
        # The memory picture fades in and out
        info = CUTSCENES[scene["number"]]
        st.html(fade_css(LIMITS["cutscene_seconds"]))
        with st.container(key="cutscene"):
            st.image(cutscene_picture(scene["number"]), width="stretch", alt=info["title"])
        st.write(f"**{info['title']}**: {info['caption']}")
    elif st.session_state.viewing and not scene:
        # The close-up the player opened with "Look closer" (until the next message)
        looking_at = st.session_state.viewing
        st.image(str(OBJECT_IMAGES[looking_at]), width="stretch",
                 alt=f"A close-up of the {CONFIG['objects'][looking_at]['name']}")
        if st.button("Back to the room", icon=":material/arrow_back:"):  # free: no move, no LLM
            st.session_state.viewing = None
            st.rerun()
    else:
        # The room, with the pixel avatar in front of the object of the last allowed action
        me = st.session_state.avatar
        alt = "Sky's attic room at night"
        if game["drawer_open"]:
            alt += ", the drawer is open"
        if me["at"] != "start":
            alt += f", you stand by the {CONFIG['objects'][me['at']]['name']}"
        st.image(room_with_avatar(game["drawer_open"], me["at"], me["facing"]), width="stretch", alt=alt)
    if scene:
        cutscene_watch()

    # Status panel (the HUD): each number has a thin bar or lock icons under it.
    # Three small blocks in a row; on a narrow screen (a phone) they wrap instead of stacking one by one.
    with st.container(border=True, horizontal=True):
        time_col = st.container(width=HUD_WIDTH)
        moves_col = st.container(width=HUD_WIDTH)
        codes_col = st.container(width=HUD_WIDTH)
        with time_col:
            if scene:
                frozen = game["deadline"] - scene["ends_at"]  # time left when the memory ends
                st.metric("Time (paused)", format_time(frozen))  # in the label: a badge made the card taller
                st.progress(bar_value(frozen, LIMITS["time_seconds"]))
            elif game["door_open"]:
                st.metric("Time left", "stopped")
            else:
                live_clock()
        with moves_col:
            st.metric("Moves", f"{game['moves']} / {LIMITS['max_moves']}")
            st.progress(bar_value(game["moves"], LIMITS["max_moves"]))
        with codes_col:
            st.metric("Wrong codes", f"{game['wrong_codes']} / {LIMITS['max_wrong_codes']}")
            st.markdown(lock_icons(game["wrong_codes"], LIMITS["max_wrong_codes"]))
    # Items: one small card per item (the picture if it exists, and always an icon and the name)
    with st.container(horizontal=True):
        if not game["inventory"]:
            st.caption(":material/backpack: No items yet")
        for item_id in game["inventory"]:
            item_name = CONFIG["items"][item_id]["name"]
            with st.container(border=True, width="content"):
                if item_id in ITEM_IMAGES and ITEM_IMAGES[item_id].exists():
                    st.image(str(ITEM_IMAGES[item_id]), width=64, alt=item_name)
                st.markdown(f"{ITEM_ICONS.get(item_id, ':material/backpack:')} **{item_name}**")
        # The diary page can be read again after the player found it (no move, no LLM).
        # It sits in the same row as the items, to save height.
        if "diary" in game["examined"] and not scene:
            if st.button("Open the diary page", icon=":material/menu_book:"):
                diary_page()

with right:
    chat_box = st.container(height=CHAT_HEIGHT)
    with chat_box:
        for message in st.session_state.messages:
            with st.chat_message(message["role"], avatar=avatars()[message["role"]]):
                if message.get("fresh"):
                    # The newest story is typed once. It is marked as shown FIRST, so a fast
                    # next message cannot make the story disappear.
                    message["fresh"] = False
                    if typewriter_on():
                        started = time.time()
                        count = max(1, len(message["content"].split(" ")))
                        st.write_stream(words(message["content"], min(TYPE_DELAY, TYPE_MAX_SECONDS / count)))
                        if not scene:  # during a memory the clock is already paused: no refund
                            game["deadline"] += time.time() - started  # typing is not the player's time
                    else:
                        st.write(message["content"])
                else:
                    st.write(message["content"])
                if message.get("note"):  # the LLM failed and a plain text was used
                    st.caption("(fallback: " + message["note"] + ")")
                if show_debug and message.get("debug"):
                    st.caption(message["debug"])
        # After the newest story: a button to open the close-up of the object (free: no move, no LLM).
        # It comes after the typed story, so the player reads first. The room with the avatar stays
        # on the left until the player clicks.
        if st.session_state.close_up and not st.session_state.viewing and not scene:
            if st.button("Look closer", icon=":material/zoom_in:"):
                st.session_state.viewing = st.session_state.close_up
                st.rerun()
        if game["door_open"] and not scene:
            # The door is open: the player decides how the story ends, in the chat under the last story
            with st.chat_message("assistant", avatar=avatars()["assistant"]):
                st.write(FINAL_CHOICE_TEXT)
                remember_col, forget_col = st.columns(2)
                if remember_col.button("Remember", type="primary", width="stretch"):
                    save_stats()
                    st.session_state.ending = "remember"
                    st.rerun()
                if forget_col.button("Forget", width="stretch"):
                    save_stats()
                    st.session_state.ending = "forget"
                    st.rerun()
    # No typing while a memory is playing, or after the door is open
    no_typing = scene or game["door_open"]
    player_text = None if no_typing else st.chat_input("Type what you do...")

    # Memories found: three small cards under the chat. Dark grey with a ? until the memory has played.
    st.caption("Memories found")
    # Three columns: they always stay in one row, each takes a third of the width.
    for column, (number, info) in zip(st.columns(3), CUTSCENES.items()):
        with column, st.container(border=True):
            # The card unlocks when the big picture shows, not during the short walk before it
            waiting = scene and scene["number"] == number and time.time() < scene["shows_at"]
            if number in game["cutscenes"] and not waiting:
                st.image(str(CUTSCENE_IMAGES[number]), width="stretch", alt=info["title"])
                st.caption(info["title"])
                # Icon only, so it fits any card width; the tooltip says what it does
                if not scene and st.button(":material/replay:", key=f"memory_{number}",
                                           help=f"Replay: {info['title']}", width="stretch"):
                    memory_page(number)
            else:
                st.image(locked_card(), width="stretch", alt="A locked memory")

if player_text:
    if time_is_up(game, time.time()):
        lose("time")
        st.rerun()
    st.session_state.messages.append({"role": "user", "content": player_text})
    waiting_since = time.time()
    # 1. the interpreter proposes an action, 2. Python decides, 3. the narrator describes the facts
    action, problem_1 = interpret(player_text, CONFIG)
    if problem_1:
        # The interpreter failed (for example Gemini is busy). It is not the player's fault:
        # nothing happens, no move is used, and the waiting time is given back.
        game["deadline"] += time.time() - waiting_since
        st.session_state.messages.append(
            {"role": "assistant", "content": TRY_AGAIN_TEXT, "note": problem_1}
        )
        st.rerun()
    count_move(game)
    outcome = handle_action(action, game, CONFIG)
    # The avatar walks only after Python ALLOWED the action (a refused action changes nothing)
    spot = goal(action, outcome["allowed"], CONFIG["objects"])
    if spot:
        me = st.session_state.avatar
        me["facing"] = facing(me["at"], spot, me["facing"])
        me["at"] = spot
    # Close-up picture: offered only after a successful examine of an object that has a picture file
    st.session_state.viewing = None
    st.session_state.close_up = None
    if outcome["allowed"] and action.get("action") == "examine":
        seen_id = find_id(action.get("target"), CONFIG["objects"])
        if seen_id in OBJECT_IMAGES and OBJECT_IMAGES[seen_id].exists():
            st.session_state.close_up = seen_id
    story, problem_2 = narrate(outcome["facts"], CONFIG)  # facts only, not the player's words
    # Waiting for Gemini is not the player's fault: give that time back
    game["deadline"] += time.time() - waiting_since
    if game["door_open"] and not game.get("door_opened_at"):
        game["door_opened_at"] = time.time()  # the clock stops for the ending stats
    verdict = "allowed" if outcome["allowed"] else "refused: " + outcome["reason"]
    st.session_state.messages.append({
        "role": "assistant",
        "content": story,
        "note": problem_2,
        "debug": f"action {action} -> {verdict}",
        "fresh": True,  # typed word by word the first time it is drawn
    })
    # Did the player just run out of moves or wrong codes?
    lost_reason = check_limits(game, CONFIG)
    if lost_reason:
        lose(lost_reason)
    elif outcome["cutscene"]:
        start_cutscene(outcome["cutscene"])
    st.rerun()
