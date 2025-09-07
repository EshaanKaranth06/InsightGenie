
import re
from html import unescape

URL_RE = re.compile(r"https?://\S+|www\.\S+")
MENTION_RE = re.compile(r"@\w+")
MULTIWS_RE = re.compile(r"\s+")

def clean_text(text: str) -> str:
    if text is None:
        return ""
    t = unescape(text)
    t = URL_RE.sub("", t)
    t = MENTION_RE.sub("", t)
    t = t.replace("\n", " ").strip()
    t = MULTIWS_RE.sub(" ", t)
    # optionally remove emojis: keep them or strip depending on needs
    return t
