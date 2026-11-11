"""Connection test: ask Gemini one question and print the answer.

Run:  python scripts/connection_test.py
Set USE_MOCK_LLM=true in .env to test without calling the API.
"""
import os

from dotenv import load_dotenv

# Read the settings from the .env file into environment variables
load_dotenv()

USE_MOCK = os.getenv("USE_MOCK_LLM", "false").lower() == "true"
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

QUESTION = "In one short sentence, describe a quiet attic room at night."


def ask_mock(question):
    # A fake answer, so we can test without internet, a key or quota
    return "[MOCK] A quiet attic room, lit only by pale light from a round window."


def ask_gemini(question):
    # Imported here so mock mode works even if the API package has a problem
    from google import genai
    from google.genai import types

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "put_your_key_here":
        raise SystemExit("No API key found. Put GEMINI_API_KEY in your .env file.")

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=MODEL,
        contents=question,
        config=types.GenerateContentConfig(
            system_instruction="You are a calm game narrator. Answer in one sentence.",
            temperature=0.7,  # 0 = very predictable, 1 = more creative
        ),
    )
    return response.text


if __name__ == "__main__":
    print("Mode :", "MOCK (no API call)" if USE_MOCK else f"REAL, model = {MODEL}")
    print("Asked:", QUESTION)
    try:
        answer = ask_mock(QUESTION) if USE_MOCK else ask_gemini(QUESTION)
        print("Answer:", answer)
    except Exception as error:
        # Show what went wrong. The error text does not contain your key.
        print("FAILED:", type(error).__name__, "-", error)
        # Gemini errors carry a number (code). Give a simple hint for common ones.
        code = getattr(error, "code", None)
        if code in (401, 403):
            print("Hint: check GEMINI_API_KEY in .env and that your project can use the free tier.")
        elif code == 404:
            print("Hint: the model name is wrong. Run scripts/list_models.py and fix GEMINI_MODEL.")
        elif code == 429:
            print("Hint: free-tier limit reached. Wait a bit, or use USE_MOCK_LLM=true.")
