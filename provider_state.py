from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ProviderStateOps:
    marked_seen_ids: list[str] = field(default_factory=list)

    def mark_seen(self, source_ids: list[str]) -> None:
        self.marked_seen_ids.extend(source_ids)
