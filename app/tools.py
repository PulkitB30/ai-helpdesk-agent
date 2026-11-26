"""The 4 tools the agent can call. Plain Python functions - no LLM here.
Each returns a dict, which we send back to the LLM as the tool result.

SECURITY: the tools never take an email from the LLM. Who the user is comes
from the login layer (CURRENT_USER), so "I am Ben" in chat cannot fool them."""
from app.db import connect, user_exists

CURRENT_USER = {"email": None}  # set by login code (SSO in real life), never by the LLM


NOT_LOGGED_IN = {"error": "No valid logged-in user. Ask the user to log in again."}


def _me() -> str | None:
    """Return the logged-in email, or None if it is not a real user (check B)."""
    email = CURRENT_USER["email"]
    return email if email and user_exists(email) else None


def check_account_status() -> dict:
    """Look up the logged-in user's account status (active/locked/disabled) and MFA."""
    if _me() is None:
        return NOT_LOGGED_IN
    with connect() as conn:
        # data minimization: only the fields the LLM needs - no email, name, department
        row = conn.execute("SELECT account_status, mfa_enabled FROM users WHERE email = ?",
                           (_me(),)).fetchone()
    return dict(row) if row else {"error": "Logged-in user not found"}


def create_ticket(summary: str, category: str, priority: str) -> dict:
    """Create a helpdesk ticket for the logged-in user.
    category: account|network|hardware|software|other. priority: low|medium|high."""
    if _me() is None:
        return NOT_LOGGED_IN
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO tickets (user_email, summary, category, priority) VALUES (?,?,?,?)",
            (_me(), summary, category, priority),
        )
    return {"ticket_id": cur.lastrowid, "status": "open"}


def get_ticket_status(ticket_id: int) -> dict:
    """Get the status of one of the logged-in user's own tickets by its ID."""
    if _me() is None:
        return NOT_LOGGED_IN
    with connect() as conn:
        row = conn.execute("SELECT id, summary, category, priority, status, created_at "
                           "FROM tickets WHERE id = ? AND user_email = ?",
                           (ticket_id, _me())).fetchone()
    return dict(row) if row else {"error": f"No ticket {ticket_id} found for you"}


def reset_password() -> dict:
    """STUB: send a password reset link to the logged-in user. Changes nothing real.
    Not allowed for disabled accounts - those need a ticket."""
    status = check_account_status()
    if "error" in status:
        return status
    if status["account_status"] == "disabled":
        return {"error": "Account is disabled. Password reset not allowed - a ticket is needed."}
    return {"result": "Reset link sent to the user's registered email (simulated)."}


TOOLS = [check_account_status, create_ticket, get_ticket_status, reset_password]
