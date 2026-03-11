from __future__ import annotations

import re
from dataclasses import dataclass, field


DATE_PATTERNS = [
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    re.compile(r"\b\d{1,2}[:.]\d{2}\b"),
    re.compile(r"\b(?:today|tomorrow|сегодня|завтра|пятниц[ауеы]?|понедельник|вторник|сред[ауеы]?|четверг|суббот[ауеы]?|воскресенье)\b", re.IGNORECASE),
]
ACTION_PATTERNS = [
    re.compile(r"\b(?:please|нужно|надо|please review|reply|confirm|submit|call|schedule|оплатить|позвонить|подтвердить|ответить)\b", re.IGNORECASE),
]


@dataclass(slots=True)
class ExtractedFacts:
    action_items: list[str] = field(default_factory=list)
    date_mentions: list[str] = field(default_factory=list)


def extract_facts(text: str) -> ExtractedFacts:
    facts = ExtractedFacts()
    sentences = re.split(r"(?<=[\.!?])\s+", text)

    for sentence in sentences:
        stripped = sentence.strip()
        if not stripped:
            continue
        if any(p.search(stripped) for p in ACTION_PATTERNS):
            facts.action_items.append(stripped)
        for pattern in DATE_PATTERNS:
            facts.date_mentions.extend(match.group(0) for match in pattern.finditer(stripped))

    facts.action_items = _dedup_preserve_order(facts.action_items)[:3]
    facts.date_mentions = _dedup_preserve_order(facts.date_mentions)[:5]
    return facts


def _dedup_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result
