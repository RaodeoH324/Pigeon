import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

from tools import TOOL_FUNCTIONS
from guard import check
import audit

load_dotenv()

MODELS = ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-3.8-flash"]
MAX_STEPS = 8

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options=types.HttpOptions(timeout=30000),
)

types.FunctionDeclaration(
        name="list_files",
        description="List the names of the files in the allowed folder. Use this when unsure of an exact file name.",
    ),

def make_declaration(name, description, params, optional=()):
    """Describe a tool to Gemini. params = {argument_name: description}."""
    return types.FunctionDeclaration(
        name=name,
        description=description,
        parameters=types.Schema(
            type="OBJECT",
            properties={
                k: types.Schema(type="STRING", description=v)
                for k, v in params.items()
            },
            required=[k for k in params if k not in optional],
        ),
    )


declarations = [
    types.FunctionDeclaration(
        name="list_files",
        description="List the names of the files in the allowed folder. Use this when unsure of an exact file name.",
    ),
    make_declaration("read_file", "Read a text, PDF or Word file from the folder.",
                     {"filename": "File name, e.g. sample.txt"}),
    make_declaration("write_file", "Write text to a file in the workspace.",
                     {"filename": "File name", "content": "Text to write"}),
    make_declaration("delete_file", "Delete a file from the workspace.",
                     {"filename": "File name"}),
    make_declaration("send_email", "Send an email, optionally with one file attached.",
                     {"to": "Recipient email address",
                      "subject": "Email subject", "body": "Email body",
                      "attachment": "Optional: name of a file in the folder to attach"},
                     optional=("attachment",)),
]

config = types.GenerateContentConfig(
    system_instruction=(
        "You are Pigeon, an assistant with file and email tools. "
        "Only say a file is attached if you passed it in the attachment argument. "
        "If a tool returns an error or a block, report that honestly."
        "If you are unsure of an exact file name, call list_files first. "
    ),
    tools=[types.Tool(function_declarations=declarations)],
    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
)


def call_model(contents):
    for model in MODELS:
        for attempt in range(2):
            try:
                return client.models.generate_content(
                    model=model, contents=contents, config=config
                )
            except Exception as e:
                print(f"  [{model}, try {attempt + 1}] {str(e)[:100]}")
                time.sleep(2)
    raise RuntimeError("All models failed. Try again in a few minutes.")

def clip(text, limit=40):
    """Cut long text down to one short piece."""
    text = str(text).replace("\n", " ")
    return text if len(text) <= limit else text[:limit] + "..."


def describe(name, args):
    """Turn a tool call into a short, readable phrase."""
    if name == "send_email":
        extra = f' with attachment {args["attachment"]}' if args.get("attachment") else ""
        return f'send an email to {args.get("to")} (subject: "{clip(args.get("subject", ""))}"){extra}'
    if name == "write_file":
        return f'write to {args.get("filename")}'
    if name == "read_file":
        return f'read {args.get("filename")}'
    if name == "delete_file":
        return f'delete {args.get("filename")}'
    if name == "list_files":
        return "list the files in PigeonReadable"
    return name

def run_agent(task):
    contents = [types.Content(role="user", parts=[types.Part(text=task)])]

    for step in range(MAX_STEPS):
        response = call_model(contents)
        contents.append(response.candidates[0].content)

        calls = response.function_calls
        if not calls:
            print("\nAgent:", response.text)
            return

        result_parts = []
        for call in calls:
            args = dict(call.args or {})
            action = describe(call.name, args)

            # THE GUARD: every action passes through here
            decision, reason = check(call.name, args)

            if decision == "ask":
                answer = input(
                    f"\n[?] Pigeon wants to {action}. "
                    f"Needs your approval: {reason}. Allow? (y/n) "
                ).strip().lower()
                decision = "ask -> approved" if answer == "y" else "ask -> rejected"

            if decision in ("allow", "ask -> approved"):
                result = TOOL_FUNCTIONS[call.name](**args)
                print(f"    [done] {action}")
            elif decision == "ask -> rejected":
                result = "BLOCKED: human did not approve"
                print(f"    [rejected] {action}")
            else:
                result = f"BLOCKED by policy: {reason}"
                print(f"    [blocked] {action}: {reason}")

            audit.log(task, call.name, args, decision, reason, result)

            result_parts.append(
                types.Part.from_function_response(
                    name=call.name, response={"result": result}
                )
            )

        contents.append(types.Content(role="user", parts=result_parts))

    print("Stopped: reached the maximum number of steps.")


if __name__ == "__main__":
    audit.init()
    task = input("What should Pigeon do? \n")
    run_agent(task)