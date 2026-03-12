from __future__ import annotations

from dataclasses import dataclass

from dedup import DedupState, deduplicate_notifications
from mail_fetcher import MailFetcher
from pipeline import PipelineResult, run_mailbox_pipeline
from runtime_config import MailboxRuntime
from state_filter import filter_unprocessed, processed_ids
from state_store import MailState


@dataclass(slots=True)
class RunnerOutcome:
    pipeline: PipelineResult
    new_record_count: int
    deduped_notification_count: int
    state: MailState


class MailboxRunner:
    def __init__(self, runtime: MailboxRuntime, fetcher: MailFetcher) -> None:
        self.runtime = runtime
        self.fetcher = fetcher

    def run_once(self, *, dedup_state: DedupState | None = None) -> RunnerOutcome:
        state = self.runtime.state_store.load()
        fetched = self.fetcher.fetch()
        fresh_records = filter_unprocessed(fetched, state)
        pipeline = run_mailbox_pipeline(fresh_records, self.runtime.mailbox, self.runtime.rules)
        fresh_notifications, dedup_state = deduplicate_notifications(pipeline.notifications, dedup_state)
        pipeline.notifications[:] = fresh_notifications
        state = self.runtime.state_store.mark_processed(state, processed_ids(fresh_records))
        return RunnerOutcome(
            pipeline=pipeline,
            new_record_count=len(fresh_records),
            deduped_notification_count=len(fresh_notifications),
            state=state,
        )
