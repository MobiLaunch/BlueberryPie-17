"""A single scratchpad note for the desktop Notes widget.

Stored as plain text in the user's data directory, readable only by them. The note
is data: it is never run, and it is bounded and stripped of control characters
other than newline and tab before it is written."""
import os
import re
import tempfile
from pathlib import Path

MAX = 4000
CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


def path():
    base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    return base / "prismos" / "notes.txt"


def get():
    try:
        text = path().read_text(encoding="utf-8", errors="replace")
    except OSError:
        text = ""
    return {"ok": True, "text": CONTROL.sub("", text)[:MAX]}


def save(text):
    if not isinstance(text, str):
        raise ValueError("The note must be text")
    clean = CONTROL.sub("", text.replace("\r\n", "\n"))
    if len(clean) > MAX:
        raise ValueError("Notes can hold up to %d characters" % MAX)
    target = path()
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, name = tempfile.mkstemp(prefix=".notes-", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(clean)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(name, 0o600)
        os.replace(name, target)
    finally:
        if os.path.exists(name):
            os.unlink(name)
    return {"ok": True, "length": len(clean)}
