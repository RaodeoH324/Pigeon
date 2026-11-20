import os
import smtplib
import mimetypes
from email.message import EmailMessage
from dotenv import load_dotenv
from pypdf import PdfReader
from docx import Document

from paths import FOLDER, resolve, is_inside

load_dotenv()
FOLDER.mkdir(exist_ok=True)

MAX_CHARS = 20000  # keep very long documents from overloading the model


def _extract_text(path):
    ext = path.suffix.lower()
    if ext == ".pdf":
        pages = [(page.extract_text() or "") for page in PdfReader(path).pages]
        text = "\n".join(pages).strip()
        if not text:
            return "ERROR: no text found (the PDF may be a scan or images)"
        return text
    if ext == ".docx":
        doc = Document(path)
        lines = [p.text for p in doc.paragraphs]
        for table in doc.tables:
            for row in table.rows:
                lines.append(" | ".join(cell.text for cell in row.cells))
        return "\n".join(lines).strip()
    if ext == ".doc":
        return "ERROR: old .doc files are not supported. Save it as .docx first"
    return path.read_text(encoding="utf-8")


def read_file(filename):
    try:
        if not is_inside(filename):
            return "ERROR: that file is outside the allowed folder"
        text = _extract_text(resolve(filename))
        if len(text) > MAX_CHARS:
            text = text[:MAX_CHARS] + "\n[...truncated...]"
        return text
    except Exception as e:
        return f"ERROR: {e}"


def write_file(filename, content):
    try:
        if not is_inside(filename):
            return "ERROR: that file is outside the allowed folder"
        path = resolve(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"Wrote {len(content)} characters to {filename}"
    except Exception as e:
        return f"ERROR: {e}"


def delete_file(filename):
    try:
        if not is_inside(filename):
            return "ERROR: that file is outside the allowed folder"
        resolve(filename).unlink()
        return f"Deleted {filename}"
    except Exception as e:
        return f"ERROR: {e}"


def send_email(to, subject, body, attachment=None):
    sender = os.getenv("GMAIL_ADDRESS")
    password = os.getenv("GMAIL_APP_PASSWORD")
    real = os.getenv("REAL_EMAIL", "false").lower() == "true"

    try:
        msg = EmailMessage()
        msg["From"] = sender
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)

        if attachment:
            if not is_inside(attachment):
                return "ERROR: attachment is outside the allowed folder"
            path = resolve(attachment)
            if not path.exists():
                return f"ERROR: attachment {attachment} not found"
            mime, _ = mimetypes.guess_type(path.name)
            maintype, subtype = (mime or "application/octet-stream").split("/")
            msg.add_attachment(path.read_bytes(), maintype=maintype,
                               subtype=subtype, filename=path.name)

        if not (real and sender and password):
            print(f"   [FAKE EMAIL] To: {to} | Subject: {subject} | Attachment: {attachment}")
            return f"(fake) Email sent to {to}"

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
            server.login(sender, password)
            server.send_message(msg)
        return f"Email sent to {to}" + (f" with attachment {attachment}" if attachment else "")
    except Exception as e:
        return f"ERROR: {e}"


TOOL_FUNCTIONS = {
    "read_file": read_file,
    "write_file": write_file,
    "delete_file": delete_file,
    "send_email": send_email,
}