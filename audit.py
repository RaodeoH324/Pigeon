import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB = Path(__file__).parent / "audit.db"


def init():
    with sqlite3.connect(DB) as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time TEXT, task TEXT, tool TEXT, args TEXT,
                decision TEXT, reason TEXT, result TEXT
            )"""
        )


def log(task, tool, args, decision, reason, result):
    with sqlite3.connect(DB) as conn:
        conn.execute(
            "INSERT INTO audit (time, task, tool, args, decision, reason, result) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (datetime.now().isoformat(timespec="seconds"), task, tool,
             json.dumps(args), decision, reason, str(result)[:300]),
        )


def show():
    with sqlite3.connect(DB) as conn:
        rows = conn.execute(
            "SELECT time, tool, args, decision, reason FROM audit ORDER BY id"
        ).fetchall()
    for time, tool, args, decision, reason in rows:
        print(f"{time} | {tool} | {decision.upper()} | {reason}\n    args: {args[:120]}")


if __name__ == "__main__":
    show()