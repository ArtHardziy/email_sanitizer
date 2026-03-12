from __future__ import annotations

from dataclasses import dataclass

from imap_client import login_imap
from live_fetcher import LiveIMAPFetcher
from provider_state import ProviderStateOps
from runner import MailboxRunner, RunnerOutcome
from runtime_config import MailboxRuntime
from secret_binding import bind_mailbox_secret
from sync_policy import decide_sync


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
        fetcher = LiveIMAPFetcher(session, mark_seen_after_fetch=False)
        runner = MailboxRunner(runtime, fetcher)
        outcome = runner.run_once()
        decision = decide_sync(
            fetched_count=outcome.new_record_count,
            notification_count=len(outcome.pipeline.notifications),
            provider_seen_mode="after_success" if mark_seen_after_fetch else "never",
            local_processed_mode="always",
        )
        if decision.mark_seen_provider and fetcher.last_fetched_ids:
            session.mark_seen(fetcher.last_fetched_ids)
            provider_state.mark_seen([mid.decode() for mid in fetcher.last_fetched_ids])
        return LiveRunResult(outcome=outcome, provider_state=provider_state)
    finally:
        session.logout()
