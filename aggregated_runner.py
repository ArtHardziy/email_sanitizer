from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from aggregate_models import AggregatedRunResult, MailboxRunError
from dedup import DedupState
from mail_fetcher import MailFetcher
from multi_runtime import MultiMailboxRuntime
from runner import MailboxRunner
from unified_reader import build_unified_messages


FetcherFactory = Callable[[str], MailFetcher]


def run_aggregated(runtime: MultiMailboxRuntime, fetcher_factory: FetcherFactory) -> AggregatedRunResult:
    notifications = []
    messages = []
    errors = []
    success_count = 0
    dedup_state = DedupState()

    enabled = runtime.enabled_mailboxes()
    for mailbox_runtime in enabled:
        try:
            fetcher = fetcher_factory(mailbox_runtime.mailbox.name)
            outcome = MailboxRunner(mailbox_runtime, fetcher).run_once(dedup_state=dedup_state)
            notifications.extend(outcome.pipeline.notifications)
            messages.extend(build_unified_messages(outcome.pipeline.processed))
            success_count += 1
        except Exception as exc:
            errors.append(
                MailboxRunError(
                    mailbox_name=mailbox_runtime.mailbox.name,
                    code=type(exc).__name__,
                    message=str(exc),
                )
            )

    failure_count = len(errors)
    result = "success"
    if success_count and failure_count:
        result = "partial_success"
    elif failure_count and not success_count:
        result = "error"

    return AggregatedRunResult(
        result=result,
        mailbox_count=len(enabled),
        success_count=success_count,
        failure_count=failure_count,
        notifications=notifications,
        messages=messages,
        errors=errors,
    )
