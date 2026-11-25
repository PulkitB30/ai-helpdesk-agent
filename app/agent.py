"""The agent loop: LLM decides -> our code runs the tool -> result goes back -> repeat.
Run: python -m app.agent"""
from app.llm import chat_step, tool_result_message, user_message
from app.tools import TOOLS

SYSTEM = """You are the IT helpdesk assistant of a small company.
Help employees with IT problems. Use the tools to look up accounts and tickets.
Always ask for the user's email if you need it and don't have it.
Create a ticket when you cannot solve the problem yourself.
Never invent account data - only use what the tools return. Be short and friendly."""

TOOLS_BY_NAME = {f.__name__: f for f in TOOLS}
MAX_STEPS = 5  # safety limit, so the loop can never run forever


def run_agent(history: list, question: str, verbose: bool = True) -> str:
    history.append(user_message(question))
    for _ in range(MAX_STEPS):
        model_msg, tool_calls, text = chat_step(history, TOOLS, SYSTEM)
        history.append(model_msg)
        if not tool_calls:          # no tool wanted -> this is the final answer
            return text
        for name, args in tool_calls:
            if verbose:
                print(f"  [tool] {name}({args})")
            func = TOOLS_BY_NAME.get(name)
            result = func(**args) if func else {"error": f"Unknown tool {name}"}
            if verbose:
                print(f"  [result] {result}")
            history.append(tool_result_message(name, result))
    return "Sorry, I could not finish this request. Please contact IT directly."


if __name__ == "__main__":
    from app.db import init_db
    init_db()
    history = []  # the conversation memory
    print("IT Helpdesk Agent - type 'quit' to exit")
    while (q := input("\nYou: ")) != "quit":
        print("Agent:", run_agent(history, q))
