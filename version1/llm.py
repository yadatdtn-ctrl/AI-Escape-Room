"""Version 1: ask the Game Master (Gemini) for a reply, or fake it in mock mode."""
import os

from dotenv import load_dotenv

from prompts import SYSTEM_INSTRUCTION

load_dotenv()  # read .env (key, model, mock switch)

# Mock mode: simple fake answers chosen by a keyword in the player's text
MOCK_REPLIES = [
    ("raincoat", "[MOCK] The yellow raincoat is still damp. In the pocket your fingers find a small brass key."),
    ("diary", "[MOCK] The diary opens easily. One line says: 'The best day of my life.'"),
    ("drawer", "[MOCK] The drawer is locked. It needs a small key."),
    ("key", "[MOCK] The brass key turns. Inside the drawer lies a vinyl record."),
    ("record", "[MOCK] The record player hums. A voice begins to speak."),
    ("door", "[MOCK] The door has a keypad for a 4-digit code."),
]
MOCK_DEFAULT = "[MOCK] The room is quiet. Nothing happens."


def use_mock():
    return os.getenv("USE_MOCK_LLM", "false").lower() == "true"


def mock_reply(text):
    text = text.lower()
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
        contents.append(types.Content(role=role, parts=[types.Part(text=m["content"])]))
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
