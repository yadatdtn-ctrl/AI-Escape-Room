"""Version 2: the Streamlit page. Python decides, the LLM only translates and describes.

Run from the project folder:  streamlit run version2/app.py
"""
import time
from pathlib import Path

import streamlit as st

from game_state import count_move, load_config, new_state
from llm import interpret, narrate, use_mock
from pictures import OBJECT_IMAGES, pick, trimmed, zoom
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
AVATAR_YOU = ASSETS / "Avatar_you.png"  # chat icon for the player (by Yada)
AVATAR_NARRATOR = ASSETS / "Avatar_narrator.png"  # chat icon for the narrator (by Yada)

# Cutscene fade-in (from the design): CSS only for the container with key="cutscene"
FADE_IN_CSS = """<style>
.st-key-cutscene img { animation: fadein 1.5s ease-in; }
@keyframes fadein { from { opacity: 0; } to { opacity: 1; } }
</style>"""

INTRO = (
    "You will wake up in a room that is not yours. "
    "Somewhere in it is a way out. Look around, collect what you find, "
    "and listen to what the room remembers."
)

HOW_TO_PLAY = f"""
- Type what you want to do in normal words, for example:
  *examine the raincoat*, *read the diary*, *take the key*,
  *open the drawer with the key*, *type 1234 on the keypad*.
- Send **one action per message**: take the key first, then read the diary.
- You have **{LIMITS["time_seconds"] // 60} minutes** and **{LIMITS["max_moves"]} moves**.
  Every message you send is 1 move. The clock starts when you press Start.
- The door allows only **{LIMITS["max_wrong_codes"]} wrong codes**.
"""

st.set_page_config(page_title="Sky - Version 2", page_icon=":material/auto_stories:", layout="wide")


@st.cache_data
def room_picture(drawer_open=False):
    """The room picture without its dark frame (cut once, then kept in Streamlit's cache).
    After the drawer is opened, the picture with the open drawer is used, if it exists."""
    path = pick(ROOM_OPEN_IMAGE, str(ROOM_IMAGE)) if drawer_open else ROOM_IMAGE
    return trimmed(path)


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
    st.session_state.cutscene = None   # the cutscene playing now: {"number": 1, "ends_at": time}
    st.session_state.viewing = None    # id of the object whose close-up picture is shown, or None


def lose(reason):
    """End the game with the bad ending."""
    st.session_state.ending = "bad"
    st.session_state.reason = reason


def format_time(seconds):
    minutes, seconds = divmod(int(seconds), 60)
    return f"{minutes}:{seconds:02d}"


def start_cutscene(number):
    """Play a cutscene and stop the clock: the player gets the seconds back."""
    seconds = LIMITS["cutscene_seconds"]
    st.session_state.cutscene = {"number": number, "ends_at": time.time() + seconds}
    st.session_state.game["deadline"] += seconds


@st.fragment(run_every=1)
def live_clock():
    """Shows the countdown. Streamlit re-runs ONLY this small part every second."""
    seconds_left = int(st.session_state.game["deadline"] - time.time())
    if seconds_left <= 0:
        lose("time")
        st.rerun()  # redraw the whole page so the bad ending appears
    st.metric("Time left", format_time(seconds_left))


@st.dialog("Sky's diary", width="medium")
def diary_page():
    """The diary page again. It shows the exact text from the config (all clues), and costs no move."""
    if DIARY_IMAGE.exists():
        st.image(str(DIARY_IMAGE), width="stretch", alt="A page of Sky's diary")
    st.markdown(CONFIG["objects"]["diary"]["examine"])


@st.fragment(run_every=0.5)
def cutscene_watch():
    """Draws nothing. Checks twice a second if the cutscene is over."""
    if time.time() >= st.session_state.cutscene["ends_at"]:
        st.session_state.cutscene = None
        st.rerun()  # redraw the whole page: back to the room and the live clock


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
    with text_side:
        st.title("Sky")
        st.write(INTRO)
        st.subheader("How to play")
        st.markdown(HOW_TO_PLAY)
        if st.button("Start", type="primary", icon=":material/play_arrow:"):
            st.session_state.screen = "game"
            game["deadline"] = time.time() + LIMITS["time_seconds"]  # the clock starts NOW
            st.rerun()
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
        if st.button("Play again", type="primary"):
            reset_game()
            st.rerun()
    st.stop()

# ---------- Game screen: picture on the left, chat on the right ----------
left, right = st.columns(2)

with left:
    scene = st.session_state.cutscene
    if scene:
        # A memory is playing: its picture fades in, and the clock is frozen
        info = CUTSCENES[scene["number"]]
        st.html(FADE_IN_CSS)
        with st.container(key="cutscene"):
            st.image(str(CUTSCENE_IMAGES[scene["number"]]), width="stretch", alt=info["title"])
        st.write(f"**{info['title']}**: {info['caption']}")
        cutscene_watch()
    elif st.session_state.viewing:
        # A close-up of the object the player just examined (until the next message)
        looking_at = st.session_state.viewing
        st.image(str(OBJECT_IMAGES[looking_at]), width="stretch",
                 alt=f"A close-up of the {CONFIG['objects'][looking_at]['name']}")
    elif game["drawer_open"]:
        st.image(room_picture(drawer_open=True), width="stretch",
                 alt="Sky's attic room at night, the drawer is open")
    else:
        st.image(room_picture(), width="stretch", alt="Sky's attic room at night")

    # Status panel: time, moves and wrong codes as small cards in one row
    with st.container(border=True, horizontal=True):
        if scene:
            frozen = game["deadline"] - scene["ends_at"]  # time left when the memory ends
            st.metric("Time left", format_time(frozen), delta="paused", delta_color="off",
                      delta_arrow="off")
        elif game["door_open"]:
            st.metric("Time left", "stopped")
        else:
            live_clock()
        st.metric("Moves", f"{game['moves']} / {LIMITS['max_moves']}")
        st.metric("Wrong codes", f"{game['wrong_codes']} / {LIMITS['max_wrong_codes']}")
    items = [CONFIG["items"][i]["name"] for i in game["inventory"]]
    st.markdown(":material/backpack: **Items:** " + (", ".join(items) if items else "none"))

    # The diary page can be read again after the player found it (no move, no LLM)
    if "diary" in game["examined"] and not scene:
        if st.button("Open the diary page", icon=":material/menu_book:"):
            diary_page()

    if game["door_open"] and not scene:
        # The door is open: the player decides how the story ends
        st.write(FINAL_CHOICE_TEXT)
        remember_col, forget_col = st.columns(2)
        if remember_col.button("Remember", type="primary", width="stretch"):
            st.session_state.ending = "remember"
            st.rerun()
        if forget_col.button("Forget", width="stretch"):
            st.session_state.ending = "forget"
            st.rerun()

with right:
    chat_box = st.container(height=520)
    with chat_box:
        for message in st.session_state.messages:
            with st.chat_message(message["role"], avatar=avatars()[message["role"]]):
                st.write(message["content"])
                if message.get("note"):  # the LLM failed and a plain text was used
                    st.caption("(fallback: " + message["note"] + ")")
                if show_debug and message.get("debug"):
                    st.caption(message["debug"])
    # No typing while a memory is playing, or after the door is open
    no_typing = scene or game["door_open"]
    player_text = None if no_typing else st.chat_input("Type what you do...")

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
    # Close-up picture: only after a successful examine of an object that has a picture file
    st.session_state.viewing = None
    if outcome["allowed"] and action.get("action") == "examine":
        seen_id = find_id(action.get("target"), CONFIG["objects"])
        if seen_id in OBJECT_IMAGES and OBJECT_IMAGES[seen_id].exists():
            st.session_state.viewing = seen_id
    story, problem_2 = narrate(outcome["facts"], CONFIG)  # facts only, not the player's words
    # Waiting for Gemini is not the player's fault: give that time back
    game["deadline"] += time.time() - waiting_since
    verdict = "allowed" if outcome["allowed"] else "refused: " + outcome["reason"]
    st.session_state.messages.append({
        "role": "assistant",
        "content": story,
        "note": problem_2,
        "debug": f"action {action} -> {verdict}",
    })
    # Did the player just run out of moves or wrong codes?
    lost_reason = check_limits(game, CONFIG)
    if lost_reason:
        lose(lost_reason)
    elif outcome["cutscene"]:
        start_cutscene(outcome["cutscene"])
    st.rerun()
