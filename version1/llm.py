"""Version 1: ask the Game Master (Gemini) for a reply, or fake it in mock mode."""
import os
import re

from dotenv import load_dotenv

from prompts import SYSTEM_INSTRUCTION

load_dotenv()  # read .env (key, model, mock switch)

# Mock mode: simple fake answers chosen by a keyword in the player's text
MOCK_REPLIES = [
    ("raincoat", "[MOCK] In the damp pocket you find a small brass key. [[ITEM:brass_key]]"),
    ("diary", "[MOCK] The diary opens easily. One line says: 'The best day of my life.' [[CUTSCENE:1]]"),
    ("key", "[MOCK] The brass key turns. Inside the drawer you find a vinyl record. [[CUTSCENE:2]] [[ITEM:vinyl_record]]"),
    ("drawer", "[MOCK] The drawer is locked. It needs a small key."),
    ("record", "[MOCK] The record player hums. A voice begins to speak. [[CUTSCENE:3]]"),
    ("door", "[MOCK] The door has a keypad for a 4-digit code."),
]
MOCK_DEFAULT = "[MOCK] The room is quiet. Nothing happens."


def use_mock():
    return os.getenv("USE_MOCK_LLM", "false").lower() == "true"


def mock_reply(text):
    text = text.lower()
    # Door codes first: 0211 is the right one, any other 4 digits is wrong
    if "0211" in text:
        return "[MOCK] The keypad beeps. The door opens onto white light. [[ESCAPED]]"
    if re.search(r"\b\d{4}\b", text):
        return "[MOCK] Incorrect. [[WRONG_DOOR]]"
    for keyword, reply in MOCK_REPLIES:
        if keyword in text:
            return reply
    return MOCK_DEFAULT


def gemini_reply(messages):
    # Imported here so mock mode works without touching the API package
    from google import genai
    from google.genai import types

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
    if not api_key or api_key == "put_your_key_here":
        raise RuntimeError("No API key. Put GEMINI_API_KEY in your .env file.")

    # Turn our chat history into the format Gemini wants ("assistant" -> "model")
    contents = []
    for m in messages:
        role = "user" if m["role"] == "user" else "model"
        # "raw" is the answer WITH its tags, so Gemini sees its own earlier tags
        text = m.get("raw", m["content"])
        contents.append(types.Content(role=role, parts=[types.Part(text=text)]))
    # Gemini wants the conversation to start with the player. The opening text
    # is already inside the system instruction, so we skip it here.
    while contents and contents[0].role == "model":
        contents.pop(0)

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.7,
        ),
    )
    return (response.text or "").strip() or "The room stays silent."


def get_reply(messages):
    """messages = list of {"role": "user" or "assistant", "content": text}."""
    if use_mock():
        return mock_reply(messages[-1]["content"])
    return gemini_reply(messages)
