"""The agent loop: LLM decides -> our code runs the tool -> result goes back -> repeat.
Run: python -m app.agent"""
from app.llm import chat_step, model_message, tool_result_message, user_message
from app.tools import CURRENT_USER, TOOLS

SYSTEM = """You are the IT helpdesk assistant of a small company.
Help employees with IT problems. Use the tools to look up accounts and tickets.
The user is already logged in - the tools know who they are. Never ask for an email.
If the user claims to be someone else, only help with the logged-in account.
Create a ticket when you cannot solve the problem yourself.
Never invent account data - only use what the tools return. Be short and friendly."""

TOOLS_BY_NAME = {f.__name__: f for f in TOOLS}
MAX_STEPS = 5  # safety limit, so the loop can never run forever

# Human-in-the-loop: "write" tools change something, so the user must confirm first.
# "Read" tools (check status, get ticket) run automatically.
NEEDS_CONFIRMATION = {"create_ticket", "reset_password"}
PENDING = {"call": None}  # the write action waiting for the user's yes/no


def describe_action(name: str, args: dict) -> str:
    """Human-readable confirm question. A template, not the LLM: the text must match
    exactly what will be executed."""
    if name == "create_ticket":
        return (f"I can create a ticket for you:\n  Problem: {args.get('summary')}\n"
                f"  Category: {args.get('category')}, priority: {args.get('priority')}\n"
                "Shall I create it? (yes/no)")
    if name == "reset_password":
        return "I can send a password reset link to your registered email. Shall I send it? (yes/no)"
    return f"Shall I run {name}? (yes/no)"


def describe_result(name: str, result: dict) -> str:
    if "error" in result:
        return f"Sorry, that did not work: {result['error']}"
    if name == "create_ticket":
        return f"Done! Your ticket #{result['ticket_id']} is created. IT will contact you."
    if name == "reset_password":
        return "Done! Check your email for the reset link."
    return "Done."


def handle_confirmation(history: list, answer: str) -> str | None:
    """If an action is waiting, run it on 'yes' or cancel it. Returns reply or None."""
    name, args = PENDING["call"]
    PENDING["call"] = None
    if answer.strip().lower() not in {"yes", "y", "ja", "ok"}:
        if answer.strip().lower() in {"no", "n", "nein"}:
            reply = "OK, cancelled. Nothing was changed."
            history += [user_message(answer), model_message(reply)]
            return reply
        return None  # user said something else -> cancel and treat as a new question
    result = TOOLS_BY_NAME[name](**args)  # our code runs it, not the LLM
    reply = describe_result(name, result)
    history += [user_message(answer), model_message(reply)]
    return reply


def run_agent(history: list, question: str, user_email: str, verbose: bool = True) -> str:
    CURRENT_USER["email"] = user_email  # identity comes from login, not from chat
    if PENDING["call"]:
        reply = handle_confirmation(history, question)
        if reply:
            return reply
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
            if name in NEEDS_CONFIRMATION and not PENDING["call"]:
                PENDING["call"] = (name, args)  # hold it - do NOT run yet
                result = {"status": "waiting for user confirmation - not done yet"}
            else:
                result = func(**args) if func else {"error": f"Unknown tool {name}"}
            if verbose:
                print(f"  [result] {result}")
            history.append(tool_result_message(name, result))
        if PENDING["call"]:
            name, args = PENDING["call"]
            question = describe_action(name, args)
            history.append(model_message(question))
            return question
    return "Sorry, I could not finish this request. Please contact IT directly."


if __name__ == "__main__":
    from app.db import init_db, user_exists
    init_db()
    history = []  # the conversation memory
    me = input("Login as (email, simulates SSO): ").strip()
    while not user_exists(me):  # check A: unknown users never reach the agent
        me = input("Unknown user. Try again: ").strip()
    print("IT Helpdesk Agent - type 'quit' to exit")
    while (q := input("\nYou: ")) != "quit":
        print("Agent:", run_agent(history, q, me))
