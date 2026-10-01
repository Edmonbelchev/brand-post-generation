import re
from html import unescape

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]*\)")
_MD_BOLD_RE = re.compile(r"\*\*([^*]+)\*\*|__([^_]+)__")
_MD_ITALIC_RE = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)|(?<!_)_([^_]+)_(?!_)")


def plain_text_from_post(post: str) -> str:
    """Extract visible text for deterministic rules and brand voice checks."""
    if not post:
        return ""

    text = post
    if "<" in text and ">" in text:
        text = _HTML_TAG_RE.sub(" ", text)
        text = unescape(text)

    text = _MD_LINK_RE.sub(r"\1", text)
    text = _MD_BOLD_RE.sub(lambda m: m.group(1) or m.group(2) or "", text)
    text = _MD_ITALIC_RE.sub(lambda m: m.group(1) or m.group(2) or "", text)

    text = re.sub(r"\s+", " ", text).strip()
    return text
