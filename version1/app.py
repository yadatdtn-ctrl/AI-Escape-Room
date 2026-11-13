"""Version 1: the Streamlit page. The LLM is the Game Master.

Run from the project folder:  streamlit run version1/app.py
"""
import time
from pathlib import Path

import streamlit as st

from llm import get_reply, use_mock
from prompts import OPENING_TEXT
from rules import check_limits, time_is_up
from settings import CUTSCENE_SECONDS, MAX_MOVES, MAX_WRONG_CODES, TIME_LIMIT_SECONDS
from tags import ITEM_NAMES, apply_tags, parse_tags
from texts import BAD_ENDING_TEXT, BAD_ENDING_TITLE, BAD_REASONS, CUTSCENES

ASSETS = Path(__file__).parent.parent / "assets"
ROOM_IMAGE = ASSETS / "Room.jpeg"
BAD_IMAGE = ASSETS / "Bad.jpeg"
CUTSCENE_IMAGES = {
    1: ASSETS / "The Pier.jpeg",
    2: ASSETS / "The Rooftop.jpeg",
    3: ASSETS / "That Night.jpeg",
}

INTRO = (
    "You will wake up in a room that is not yours. "
    "Somewhere in it is a way out. Look around, collect what you find, "
    "and listen to what the room remembers."
)

HOW_TO_PLAY = f"""
- Type what you want to do in normal words, for example:
  *examine the raincoat*, *read the diary*, *open the drawer with the key*,
  *type 1234 on the keypad*.
- You have **{TIME_LIMIT_SECONDS // 60} minutes** and **{MAX_MOVES} moves**.
  Every message you send is 1 move. The clock starts when you press Start.
- The door allows only **{MAX_WRONG_CODES} wrong codes**.
"""

st.set_page_config(page_title="Sky - Version 1", layout="wide")


def reset_game():
    """Put the game back to the start (used at the beginning and by Restart)."""
    st.session_state.screen = "start"
    st.session_state.messages = [{"role": "assistant", "content": OPENING_TEXT}]
    st.session_state.moves = 0
    st.session_state.inventory = []    # items the player carries, e.g. "brass_key"
    st.session_state.cutscenes = []    # numbers of cutscenes already triggered
    st.session_state.wrong_codes = 0   # wrong codes typed at the door
    st.session_state.escaped = False   # True when the Game Master says the door opened
    st.session_state.deadline = None   # the moment the clock runs out (set at Start)
    st.session_state.ending = None     # None while playing, "bad" when the player loses
    st.session_state.reason = None     # why the player lost: "time", "moves" or "codes"
    st.session_state.cutscene = None   # the cutscene playing now: {"number": 1, "ends_at": time}


def lose(reason):
    """End the game with the bad ending."""
    st.session_state.ending = "bad"
    st.session_state.reason = reason


def format_time(seconds):
    minutes, seconds = divmod(int(seconds), 60)
    return f"{minutes}:{seconds:02d}"


def start_cutscene(number):
    """Play a cutscene and stop the clock: the player gets the seconds back."""
    st.session_state.cutscene = {"number": number, "ends_at": time.time() + CUTSCENE_SECONDS}
    st.session_state.deadline += CUTSCENE_SECONDS


@st.fragment(run_every=1)
def live_clock():
    """Shows the countdown. Streamlit re-runs ONLY this small part every second."""
    seconds_left = int(st.session_state.deadline - time.time())
    if seconds_left <= 0:
        lose("time")
        st.rerun()  # redraw the whole page so the bad ending appears
    st.write(f"⏱ Time left: {format_time(seconds_left)}")


@st.fragment(run_every=0.5)
def cutscene_watch():
    """Draws nothing. Checks twice a second if the cutscene is over."""
    if time.time() >= st.session_state.cutscene["ends_at"]:
        st.session_state.cutscene = None
        st.rerun()  # redraw the whole page: back to the room and the live clock


# session_state = memory that Streamlit keeps while the page is open
if "screen" not in st.session_state:
    reset_game()

# ---------- Sidebar: always visible ----------
with st.sidebar:
    st.header("Sky")
    with st.expander("How to play", expanded=False):
        st.markdown(HOW_TO_PLAY)
    if st.button("Restart"):
        reset_game()
        st.rerun()
    if use_mock():
        st.caption("Mock mode: fake answers, no API calls.")

# ---------- Start screen ----------
if st.session_state.screen == "start":
    st.title("Sky")
    st.write(INTRO)
    st.subheader("How to play")
    st.markdown(HOW_TO_PLAY)
    if st.button("Start", type="primary"):
        st.session_state.screen = "game"
        st.session_state.deadline = time.time() + TIME_LIMIT_SECONDS  # the clock starts NOW
        st.rerun()
    st.stop()

# ---------- Bad ending screen ----------
if st.session_state.ending == "bad":
    st.title(BAD_ENDING_TITLE)
    st.image(str(BAD_IMAGE), width="stretch")
    st.caption(BAD_REASONS[st.session_state.reason])
    st.write(BAD_ENDING_TEXT)
    if st.button("Play again", type="primary"):
        reset_game()
        st.rerun()
    st.stop()

# ---------- Game screen: picture on the left, chat on the right ----------
left, right = st.columns(2)

with left:
    scene = st.session_state.cutscene
    if scene:
        # A memory is playing: show its picture and caption, and freeze the clock
        st.image(str(CUTSCENE_IMAGES[scene["number"]]), width="stretch")
        info = CUTSCENES[scene["number"]]
        st.write(f"**{info['title']}**: {info['caption']}")
        frozen = st.session_state.deadline - scene["ends_at"]  # time left when it ends
        st.write(f"⏱ Time left: {format_time(frozen)} (paused)")
        cutscene_watch()
    else:
        st.image(str(ROOM_IMAGE), width="stretch")
        if st.session_state.escaped:
            st.write("⏱ The clock has stopped.")
        else:
            live_clock()
    st.write(f"👣 Moves: {st.session_state.moves} / {MAX_MOVES}")
    items = [ITEM_NAMES[i] for i in st.session_state.inventory]
    st.write("🔑 Items: " + (", ".join(items) if items else "none"))
    st.write(f"🚪 Wrong door codes: {st.session_state.wrong_codes} / {MAX_WRONG_CODES}")
    if st.session_state.escaped:
        st.success("The door opens onto white light. (The final choice comes in M4d.)")

with right:
    chat_box = st.container(height=520)
    with chat_box:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
    # No typing while a memory is playing
    player_text = None if scene else st.chat_input("Type what you do...")

if player_text:
    if time_is_up(st.session_state, time.time()):
        lose("time")
        st.rerun()
    st.session_state.messages.append({"role": "user", "content": player_text})
    st.session_state.moves += 1
    waiting_since = time.time()
    try:
        reply = get_reply(st.session_state.messages)
    except Exception as error:
        # Show a clear message instead of a crash (the text never contains the key)
        reply = f"(Game Master error: {type(error).__name__} - {error})"
    # Waiting for Gemini is not the player's fault: give that time back
    st.session_state.deadline += time.time() - waiting_since
    # Cut the hidden tags out of the text, then let them change the game state
    clean_reply, tags = parse_tags(reply)
    new_cutscenes = apply_tags(tags, st.session_state)
    st.session_state.messages.append(
        {"role": "assistant", "content": clean_reply or "The room stays silent.", "raw": reply}
    )
    # Did the player just run out of moves or wrong codes?
    lost_reason = check_limits(st.session_state)
    if lost_reason:
        lose(lost_reason)
    elif new_cutscenes:
        start_cutscene(new_cutscenes[0])  # if there are several, we play the first
    st.rerun()
