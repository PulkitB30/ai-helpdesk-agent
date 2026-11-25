"""Small wrapper around the LLM. Only this file knows we use Gemini."""
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()  # reads .env into environment variables

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")


def ask(prompt: str) -> str:
    """Send one prompt, return the text answer."""
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return response.text
