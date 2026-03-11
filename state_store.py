from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class MailState:
    processed_ids: set[str] = field(default_factory=set)


class JsonStateStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> MailState:
        if not self.path.exists():
            return MailState()
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return MailState(processed_ids=set(raw.get("processed_ids", [])))

    def save(self, state: MailState) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"processed_ids": sorted(state.processed_ids)}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def mark_processed(self, state: MailState, source_ids: list[str]) -> MailState:
        state.processed_ids.update(source_ids)
        self.save(state)
        return state
