from __future__ import annotations

import os

from config import MailboxConfig
from merge_config import merge_mailbox_with_env, secrets_from_env
from sync_policy import decide_sync


def test_merge_mailbox_with_env_overrides() -> None:
    os.environ["EMAIL_SANITIZER_PERSONAL_HOST"] = "imap.override.example.com"
    os.environ["EMAIL_SANITIZER_PERSONAL_PORT"] = "1993"
    mailbox = MailboxConfig(name="personal", host="imap.example.com", port=993, username="user@example.com")
    merged = merge_mailbox_with_env(mailbox)
    assert merged.host == "imap.override.example.com"
    assert merged.port == 1993
    del os.environ["EMAIL_SANITIZER_PERSONAL_HOST"]
    del os.environ["EMAIL_SANITIZER_PERSONAL_PORT"]


def test_secrets_from_env_builds_expected_names() -> None:
    secrets = secrets_from_env("personal")
    assert secrets.password_env == "EMAIL_SANITIZER_PERSONAL_PASSWORD"


def test_sync_policy_after_success() -> None:
    decision = decide_sync(fetched_count=2, notification_count=1, provider_seen_mode="after_success", local_processed_mode="always")
    assert decision.mark_seen_provider is True
    assert decision.mark_processed_local is True


def run_tests() -> None:
    tests = [
        test_merge_mailbox_with_env_overrides,
        test_secrets_from_env_builds_expected_names,
        test_sync_policy_after_success,
    ]
    for test in tests:
        test()
    print(f"ok: {len(tests)} merge/sync tests passed")


if __name__ == "__main__":
    run_tests()
