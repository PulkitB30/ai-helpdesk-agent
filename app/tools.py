"""The 4 tools the agent can call. Plain Python functions - no LLM here.
Each returns a dict, which we later send back to the LLM as the tool result."""
from app.db import connect


def check_account_status(email: str) -> dict:
    """Look up a user's account status (active / locked / disabled) and MFA."""
    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if row is None:
        return {"error": f"No user found with email {email}"}
    return dict(row)


def create_ticket(email: str, summary: str, category: str, priority: str) -> dict:
    """Create a helpdesk ticket. category: account|network|hardware|software|other.
    priority: low|medium|high."""
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO tickets (user_email, summary, category, priority) VALUES (?,?,?,?)",
            (email, summary, category, priority),
        )
    return {"ticket_id": cur.lastrowid, "status": "open"}


def get_ticket_status(ticket_id: int) -> dict:
    """Get the current status of a ticket by its ID."""
    with connect() as conn:
        row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    return dict(row) if row else {"error": f"No ticket with id {ticket_id}"}


def reset_password(email: str) -> dict:
    """STUB: request a password reset. Does not change any real account.
    Only allowed for active or locked accounts - disabled accounts need IT."""
    status = check_account_status(email)
    if "error" in status:
        return status
    if status["account_status"] == "disabled":
        return {"error": "Account is disabled. Password reset not allowed - a ticket is needed."}
    return {"result": f"Reset link sent to {email} (simulated)."}


TOOLS = [check_account_status, create_ticket, get_ticket_status, reset_password]
