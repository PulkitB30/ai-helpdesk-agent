# AI Helpdesk Agent

An IT-helpdesk AI agent that answers employees' IT questions from internal docs (RAG),
classifies and routes tickets, and calls tools (create ticket, check account, reset password).

> Work in progress.

## Setup
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then put your Gemini API key in .env
python -m scripts.check_key
```
