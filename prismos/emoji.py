"""Emoji picker support: copy one emoji to the clipboard and remember the ones used lately.

The picker's text comes from the shell, so it is checked here: a few code points, only
symbols, joiners, variation selectors and tag characters (plus the keycap form of a digit,
# or *). Nothing else can reach the clipboard or the settings file through this command."""
import re
import shutil
import subprocess
import unicodedata

from . import settings
from .system import CommandError

MAX_CODEPOINTS = 16
MAX_RECENT = 24
SYMBOL_CATEGORIES = {"So", "Sk", "Sm", "Cf", "Mn", "Me"}
# A few emoji are punctuation or letters in the Unicode tables; and Python's tables may be
# older than the emoji list, so unassigned code points in the emoji blocks are allowed too.
EXTRA = frozenset("\u203c\u2049\u3030\u303d\u2139")
KEYCAP = re.compile(r"[0-9#*]️?⃣\Z")


def valid(text):
    if not isinstance(text, str) or not 1 <= len(text) <= MAX_CODEPOINTS:
        return False
    if KEYCAP.fullmatch(text):
        return True
    return all(char in EXTRA or unicodedata.category(char) in SYMBOL_CATEGORIES
               or (unicodedata.category(char) == "Cn" and 0x1F000 <= ord(char) <= 0x1FAFF) for char in text)


def clean(text):
    if not valid(text):
        raise ValueError("That is not an emoji")
    return text


def recent():
    return {"ok": True, "recent": settings.load()["recent_emoji"]}


def copy(text):
    text = clean(text)
    if not shutil.which("wl-copy"):
        raise CommandError("wl-copy is not installed")
    outcome = subprocess.run(["wl-copy"], input=text.encode(), timeout=8, check=False,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if outcome.returncode:
        raise CommandError("Could not copy to the clipboard")
    try:  # Recents are a convenience; a settings problem never fails the copy.
        settings.modify(lambda data: {**data, "recent_emoji": [text] + [
            item for item in data["recent_emoji"] if item != text][:MAX_RECENT - 1]})
    except OSError:
        pass
    return {"ok": True, "copied": text}
