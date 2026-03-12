from __future__ import annotations

from dataclasses import dataclass

from imap_client import login_imap
from live_fetcher import LiveIMAPFetcher
from provider_state import ProviderStateOps
from runner import MailboxRunner, RunnerOutcome
from runtime_config import MailboxRuntime
from secret_binding import bind_mailbox_secret


@dataclass(slots=True)
class LiveRunResult:
    outcome: RunnerOutcome
    provider_state: ProviderStateOps


def run_live_cycle(runtime: MailboxRuntime, *, mark_seen_after_fetch: bool = False) -> LiveRunResult:
    bound = bind_mailbox_secret(runtime.mailbox, runtime.secrets)
    if not bound.resolved_secret:
        raise ValueError(f"No secret resolved for mailbox: {runtime.mailbox.name}")

    session = login_imap(runtime.mailbox, bound.resolved_secret)
    provider_state = ProviderStateOps()
    try:
        fetcher = LiveIMAPFetcher(session, mark_seen_after_fetch=mark_seen_after_fetch)
        runner = MailboxRunner(runtime, fetcher)
        outcome = runner.run_once()
        if mark_seen_after_fetch and fetcher.last_fetched_ids:
            provider_state.mark_seen([mid.decode() for mid in fetcher.last_fetched_ids])
        return LiveRunResult(outcome=outcome, provider_state=provider_state)
    finally:
        session.logout()
