"""Print the Gemini models your API key can use, so you can pick GEMINI_MODEL.

Run:  python scripts/list_models.py
"""
import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key or api_key == "put_your_key_here":
    raise SystemExit("No API key found. Put GEMINI_API_KEY in your .env file.")

client = genai.Client(api_key=api_key)

print("Models that can generate text (copy the part after 'models/' into .env):")
for model in client.models.list():
    # Only show models that can answer chat-like requests
    if "generateContent" in (model.supported_actions or []):
        print(" -", model.name)
