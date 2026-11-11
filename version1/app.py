"""Version 1: the Streamlit page. The LLM is the Game Master.

Run from the project folder:  streamlit run version1/app.py
"""
from pathlib import Path

import streamlit as st

from llm import get_reply, use_mock
from prompts import OPENING_TEXT
from tags import ITEM_NAMES, apply_tags, parse_tags

MAX_MOVES = 30
MAX_WRONG_CODES = 3
ROOM_IMAGE = Path(__file__).parent.parent / "assets" / "Room.jpeg"

INTRO = (
    "You will wake up in a room that is not yours. "
    "Somewhere in it is a way out. Look around, collect what you find, "
    "and listen to what the room remembers."
)

HOW_TO_PLAY = """
- Type what you want to do in normal words, for example:
  *examine the raincoat*, *read the diary*, *open the drawer with the key*,
  *type 1234 on the keypad*.
- You have **30 moves**. Every message you send is 1 move.
- The door allows only **3 wrong codes**.
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
        st.rerun()
    st.stop()

# ---------- Game screen: picture on the left, chat on the right ----------
left, right = st.columns(2)

with left:
    st.image(str(ROOM_IMAGE), width="stretch")
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
    player_text = st.chat_input("Type what you do...")

if player_text:
    st.session_state.messages.append({"role": "user", "content": player_text})
    st.session_state.moves += 1
    try:
        reply = get_reply(st.session_state.messages)
    except Exception as error:
        # Show a clear message instead of a crash (the text never contains the key)
        reply = f"(Game Master error: {type(error).__name__} - {error})"
    # Cut the hidden tags out of the text, then let them change the game state
    clean_reply, tags = parse_tags(reply)
    apply_tags(tags, st.session_state)
    st.session_state.messages.append(
        {"role": "assistant", "content": clean_reply or "The room stays silent.", "raw": reply}
    )
    st.rerun()
