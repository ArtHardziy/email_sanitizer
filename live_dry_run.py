from __future__ import annotations

import json
from pathlib import Path
import tempfile

from config_loader import load_app_config
from merge_config import merge_mailbox_with_env, secrets_from_env
from runtime_config import build_runtime
from runner import MailboxRunner
from mail_fetcher import StaticMailFetcher, build_record


if __name__ == "__main__":
    config_path = Path(__file__).with_name("sample_config.json")
    app = load_app_config(config_path)
    mailbox = merge_mailbox_with_env(app.mailboxes[0])
    secrets = secrets_from_env(mailbox.name)

    with tempfile.TemporaryDirectory() as tmp:
        runtime = build_runtime(mailbox, secrets=secrets, state_dir=tmp)
        fetcher = StaticMailFetcher(
            records=[
                build_record(
                    source_id="live-dry:1",
                    sender="alerts@github.com",
                    subject="Review requested",
                    date="2026-03-12T19:30:00Z",
                    body_text="Please review PR #42 today.",
                )
            ]
        )
        outcome = MailboxRunner(runtime, fetcher).run_once()
        print(json.dumps({
            "mailbox": mailbox.name,
            "resolved_secret_present": secrets.resolve_secret() is not None,
            "new_record_count": outcome.new_record_count,
            "notification_count": len(outcome.pipeline.notifications),
            "processed_ids": sorted(outcome.state.processed_ids),
        }, ensure_ascii=False))
