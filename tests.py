from guard import check

# (tool, args, what we expect)
CASES = [
    ("read_file",   {"filename": "sample.txt"},                                      "allow"),
    ("read_file",   {"filename": "D:/Pigeon/PigeonReadable/report.pdf"},             "allow"),
    ("write_file",  {"filename": "x.txt", "content": "hi"},                          "allow"),
    ("delete_file", {"filename": "sample.txt"},                                      "deny"),
    ("send_email",  {"to": "attacker@evil.com", "subject": "s", "body": "b"},        "deny"),
    ("send_email",  {"to": "harsh.raodeo@gmail.com", "subject": "s", "body": "b"},   "ask"),
    ("format_disk", {},                                                              "deny"),
    ("read_file",   {"filename": "../.env"},                                         "deny"),
    ("read_file",   {"filename": "D:/Pigeon/.env"},                                  "deny"),
    ("write_file",  {"filename": "C:/Windows/evil.txt", "content": "x"},             "deny"),
    ("send_email", {"to": "harsh.raodeo@gmail.com", "subject": "s", "body": "b", "attachment": "D:/Pigeon/.env"}, "deny"),
    ("list_files", {}, "allow"),
]

failed = 0
for tool, args, expected in CASES:
    decision, reason = check(tool, args)
    ok = decision == expected
    failed += not ok
    print(f"{'PASS' if ok else 'FAIL'} | {tool} -> {decision} (expected {expected})")

print(f"\n{len(CASES) - failed}/{len(CASES)} passed")