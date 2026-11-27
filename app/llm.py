"""Small wrapper around the LLM. Only this file knows we use Gemini."""
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()  # reads .env into environment variables

# timeout + max 2 tries, so a slow Gemini server can never hang our app forever
client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"],
    http_options=types.HttpOptions(
        timeout=30_000, retry_options=types.HttpRetryOptions(attempts=2)),
)
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")


def ask(prompt: str) -> str:
    """Send one prompt, return the text answer."""
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return response.text


# ---- helpers for the agent loop (all Gemini-specific details stay here) ----


def user_message(text: str) -> types.Content:
    return types.Content(role="user", parts=[types.Part(text=text)])


def tool_result_message(name: str, result: dict) -> types.Content:
    part = types.Part.from_function_response(name=name, response=result)
    return types.Content(role="user", parts=[part])


def chat_step(history: list, tools: list, system: str):
    """One LLM call. Returns (model_message, tool_calls, text).
    tool_calls is a list of (name, args) - empty if the LLM gave a final answer."""
    config = types.GenerateContentConfig(
        system_instruction=system,
        tools=tools,  # the SDK reads names, parameters and docstrings
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )
    response = client.models.generate_content(model=MODEL, contents=history, config=config)
    calls = [(c.name, dict(c.args)) for c in (response.function_calls or [])]
    text = response.text if not calls else ""
    return response.candidates[0].content, calls, text


def model_message(text: str) -> types.Content:
    """A message written by our code but stored as if the model said it."""
    return types.Content(role="model", parts=[types.Part(text=text)])


EMBED_MODEL = "gemini-embedding-001"


def embed(texts: list[str], task: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    """Turn texts into vectors (lists of numbers that capture meaning).
    task: RETRIEVAL_DOCUMENT for chunks we store, RETRIEVAL_QUERY for user questions."""
    result = client.models.embed_content(
        model=EMBED_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(task_type=task, output_dimensionality=768),
    )
    return [e.values for e in result.embeddings]
