import re
from html import escape, unescape
from html.parser import HTMLParser

_ALLOWED_TAGS = frozenset({"p", "br", "b", "strong", "i", "em", "u", "a", "div"})
_HAS_HTML_TAG = re.compile(r"<[a-z][\s>]", re.I)


def _escape_attr(value: str) -> str:
    return escape(value, quote=True)


class _PostHTMLSanitizer(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._out: list[str] = []
        self._anchor_href: str | None = None
        self._anchor_has_visible_text = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag not in _ALLOWED_TAGS:
            return
        if tag == "br":
            self._out.append("<br>")
            return
        if tag == "a":
            attr_map = {k.lower(): (v or "") for k, v in attrs}
            href = attr_map.get("href", "").strip()
            if not re.match(r"^https?://", href, re.I):
                return
            self._anchor_href = href
            self._anchor_has_visible_text = False
            self._out.append(
                f'<a href="{_escape_attr(href)}" target="_blank" rel="noopener noreferrer">'
            )
            return
        self._out.append(f"<{tag}>")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag not in _ALLOWED_TAGS or tag == "br":
            return
        if tag == "a" and self._anchor_href:
            if not self._anchor_has_visible_text:
                self._out.append(escape(self._anchor_href))
            self._anchor_href = None
            self._anchor_has_visible_text = False
        self._out.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        if self._anchor_href and data.strip():
            self._anchor_has_visible_text = True
        self._out.append(escape(data))

    def handle_entityref(self, name: str) -> None:
        self._out.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self._out.append(f"&#{name};")

    def get_html(self) -> str:
        return "".join(self._out).strip()


def plain_text_to_html(text: str) -> str:
    blocks = [b.strip() for b in re.split(r"\n\n+", text) if b.strip()]
    if not blocks:
        return ""
    parts: list[str] = []
    for block in blocks:
        inner = escape(block).replace("\n", "<br>")
        parts.append(f"<p>{inner}</p>")
    return "".join(parts)


def sanitize_post_html(html: str) -> str:
    parser = _PostHTMLSanitizer()
    parser.feed(html)
    parser.close()
    return parser.get_html()


def normalize_post_content(raw: str) -> str:
    """Normalize LLM output to safe HTML for storage and the editor."""
    text = raw.strip()
    if not text:
        return ""

    if _HAS_HTML_TAG.search(text):
        cleaned = sanitize_post_html(text)
        if cleaned:
            return cleaned
        # Fallback if parser stripped everything
        return plain_text_to_html(unescape(re.sub(r"<[^>]+>", " ", text)))

    return plain_text_to_html(text)
