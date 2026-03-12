from __future__ import annotations

import tempfile
from pathlib import Path

from aggregated_runner import run_aggregated
from mail_fetcher import StaticMailFetcher, build_record
from multi_runtime_loader import load_multi_runtime


def test_aggregated_runner_partial_success_contract() -> None:
    config_path = Path(__file__).with_name("multi_mailbox_config_sample.json")
    with tempfile.TemporaryDirectory() as tmp:
        runtime = load_multi_runtime(user_id="user-1", config_path=config_path, state_dir=tmp)

        fixtures = {
            "gmail-main": StaticMailFetcher(records=[
                build_record(
                    source_id="imap:gmail-main:1",
                    sender="alerts@github.com",
                    subject="Review requested",
                    date="2026-03-12T20:00:00Z",
                    body_text="Please review PR #42 today.",
                )
            ])
        }

        def factory(name: str):
            if name not in fixtures:
                raise RuntimeError("fetcher missing")
            return fixtures[name]

        result = run_aggregated(runtime, factory)
        assert result.result == "partial_success"
        assert result.success_count == 1
        assert result.failure_count == 1


def test_aggregated_runner_collects_messages() -> None:
    config_path = Path(__file__).with_name("multi_mailbox_config_sample.json")
    with tempfile.TemporaryDirectory() as tmp:
        runtime = load_multi_runtime(user_id="user-1", config_path=config_path, state_dir=tmp)

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
            "yandex-main": StaticMailFetcher(records=[]),
        }

        result = run_aggregated(runtime, lambda name: fixtures[name])
        assert result.result == "success"
        assert len(result.messages) == 1
        assert result.messages[0].mailbox_name == "gmail-main"


def run_tests() -> None:
    tests = [test_aggregated_runner_partial_success_contract, test_aggregated_runner_collects_messages]
    for test in tests:
        test()
    print(f"ok: {len(tests)} aggregated runner tests passed")


if __name__ == "__main__":
    run_tests()
