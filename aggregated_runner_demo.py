from __future__ import annotations

import json
import tempfile
from pathlib import Path

from mail_fetcher import StaticMailFetcher, build_record
from aggregated_runner import run_aggregated
from multi_runtime_loader import load_multi_runtime


if __name__ == "__main__":
    config_path = Path(__file__).with_name("multi_mailbox_config_sample.json")
    with tempfile.TemporaryDirectory() as tmp:
        runtime = load_multi_runtime(user_id="demo-user", config_path=config_path, state_dir=tmp)

        fixtures = {
            "gmail-main": StaticMailFetcher(records=[
                build_record(
                    source_id="imap:gmail-main:1",
                    sender="alerts@github.com",
                    subject="Review requested",
                    date="2026-03-12T20:00:00Z",
                    body_text="Please review PR #42 today.",
                )
            ]),
            "yandex-main": StaticMailFetcher(records=[
                build_record(
                    source_id="imap:yandex-main:1",
                    sender="clinic@example.com",
                    subject="Порядок сдачи анализов",
                    date="2026-03-12T20:01:00Z",
                    body_text="Пожалуйста, сдайте анализ и обратитесь к врачу после получения результата.",
                )
            ]),
        }

        result = run_aggregated(runtime, lambda mailbox_name: fixtures[mailbox_name])
        print(json.dumps({
            "result": result.result,
            "mailboxCount": result.mailbox_count,
            "successCount": result.success_count,
            "failureCount": result.failure_count,
            "notificationCount": len(result.notifications),
            "messageCount": len(result.messages),
        }, ensure_ascii=False))
