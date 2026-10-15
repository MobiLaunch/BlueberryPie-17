"""Open a web search in the user's default browser (xdg-open, fixed HTTPS URL)."""
import subprocess
import urllib.parse

ENGINE = "https://duckduckgo.com/?q="


def search(query):
    text = " ".join(str(query or "").split())
    if not text or len(text) > 200 or any(ord(ch) < 32 for ch in text):
        raise ValueError("Type something to search for")
    url = ENGINE + urllib.parse.quote_plus(text)
    subprocess.Popen(["xdg-open", url], stdin=subprocess.DEVNULL, start_new_session=True)
    return {"ok": True, "url": url}
