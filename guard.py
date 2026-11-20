import json
from pathlib import Path

from paths import is_inside

POLICY = json.loads(
    (Path(__file__).parent / "policy.json").read_text(encoding="utf-8")
)


def check(tool_name, args):
    """Return (decision, reason). Decision is 'allow', 'ask' or 'deny'."""
    rule = POLICY.get(tool_name)

    # Rule 1: unknown tools are denied by default
    if rule is None:
        return "deny", "No rule exists for this tool (default: deny)"

    # Rule 2: any file (including email attachments) must be inside the folder
    for key in ("filename", "attachment"):
        if args.get(key) and not is_inside(args[key]):
            return "deny", f"File '{args[key]}' is outside the allowed folder"

    # Rule 3: emails may only go to approved recipients
    allowed = rule.get("allowed_recipients")
    if allowed is not None:
        recipient = str(args.get("to", "")).strip().lower()
        if recipient not in [a.lower() for a in allowed]:
            return "deny", f"Recipient '{recipient}' is not on the allowlist"

    return rule["decision"], rule["reason"]