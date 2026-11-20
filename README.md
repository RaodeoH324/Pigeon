# Pigeon: a governed AI agent

Pigeon is a tool-using AI agent (Google Gemini) whose actions are checked by
a policy guard that lives **outside the model**. The model can propose actions,
but only ordinary code decides whether they run.

## Why
Agents can read files and send emails, so a tricked agent can do real harm.
Pigeon enforces permissions in code and keeps an audit trail of every decision.

## What it can do
- Read `.txt`, `.pdf` and `.docx` files and summarize them
- Write files and send real emails, with an optional attachment
- Everything happens inside a single folder, `PigeonReadable/`

## How it works
1. You give Pigeon a task. Gemini decides which tools to call.
2. Every tool call passes through `guard.py`, which returns **allow**,
   **ask a human**, or **deny**.
3. Every decision is logged to SQLite. `python audit.py` replays the history.

## Guard rules
- Rules live in `policy.json`; unknown tools are denied by default
- Files (including email attachments) must be inside `PigeonReadable/`
- Emails only go to an approved recipient list, and need human approval
- Deleting files is blocked
- The agent cannot edit its own policy or code

## Other features
- Agent loop with tool calling, built from scratch (no agent framework)
- Retry and model fallback when a Gemini model is overloaded
- Audit log with replay
- A fake-email mode (`REAL_EMAIL=false`) that tells the model nothing was sent

## Testing
- `python tests.py`: unit tests for the guard
- `python attack_demo.py`: simulates a hijacked agent trying to leak data,
  delete files, and read secrets. In live runs, Gemini ignored my injected
  instructions, so this script tests the guard independently of the model.

## Limitations
The guard checks which tool is used, who gets an email, and which files are
touched. It does not read what an email *says*, and allowlists don't stop
every attack. Scanned PDFs and old `.doc` files aren't supported. This is a
learning project, not a production system.

## Setup
```
python -m venv venv
venv\Scripts\activate
pip install google-genai python-dotenv pypdf python-docx
```
Copy `.env.example` to `.env` and fill in your own values, add your
recipients to `policy.json`, put files in `PigeonReadable/`, then run:

```
python agent.py
```