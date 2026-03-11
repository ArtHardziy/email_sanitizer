from __future__ import annotations

import html
import re

TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")
SCRIPT_STYLE_RE = re.compile(r"<(script|style).*?>.*?</\1>", re.IGNORECASE | re.DOTALL)


def html_to_text(value: str) -> str:
    cleaned = SCRIPT_STYLE_RE.sub(" ", value)
    cleaned = TAG_RE.sub(" ", cleaned)
    cleaned = html.unescape(cleaned)
    cleaned = WS_RE.sub(" ", cleaned)
    return cleaned.strip()
