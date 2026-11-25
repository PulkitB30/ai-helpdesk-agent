"""Run: python -m scripts.check_key  -> proves the API key works."""
from app.llm import ask

print(ask("Reply with exactly: Gemini works"))
