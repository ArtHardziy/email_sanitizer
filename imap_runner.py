from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from config import MailboxConfig
from imap_adapter import IMAPFetcher
from mailbox_rules import SenderDomainRules
from pipeline import PipelineResult, run_mailbox_pipeline
from secrets_config import MailboxSecrets
from state_store import JsonStateStore


@dataclass(slots=True)
class RunnerContext:
    mailbox: MailboxConfig
    secrets: MailboxSecrets
    rules: SenderDomainRules
    state_store: JsonStateStore


def run_imap_cycle(context: RunnerContext) -> PipelineResult:
    """Skeleton for real mailbox cycles.

    This intentionally stops before real authenticated fetching until secrets and
    runtime wiring are connected by a local operator-owned integration layer.
    """
    secret = context.secrets.resolve_secret()
    if not secret:
        raise ValueError("No mailbox secret resolved from environment")

    fetcher = IMAPFetcher(context.mailbox)
    raise NotImplementedError("Authenticated IMAP run is intentionally not wired yet; use local operator-owned integration")
