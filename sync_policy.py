from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SyncDecision:
    mark_seen_provider: bool
    mark_processed_local: bool
    rationale: str


@dataclass(slots=True)
class SyncPolicy:
    provider_seen_mode: str = "after_success"
    local_processed_mode: str = "always"


def decide_sync(*, fetched_count: int, notification_count: int, provider_seen_mode: str = "after_success", local_processed_mode: str = "always") -> SyncDecision:
    if fetched_count <= 0:
        return SyncDecision(False, False, "no_records")

    mark_seen = provider_seen_mode in {"always", "after_success"}
    mark_processed = local_processed_mode == "always"

    if provider_seen_mode == "never":
        mark_seen = False
    if local_processed_mode == "never":
        mark_processed = False

    rationale = f"provider={provider_seen_mode};local={local_processed_mode};notifications={notification_count}"
    return SyncDecision(mark_seen, mark_processed, rationale)
