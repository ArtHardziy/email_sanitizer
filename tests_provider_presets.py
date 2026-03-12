from __future__ import annotations

from config import MailboxConfig
from provider_presets import ProviderId, AuthMode, apply_provider_preset, get_provider_preset, supported_providers


def test_get_provider_preset_gmail() -> None:
    preset = get_provider_preset("gmail")
    assert preset.provider_id == ProviderId.GMAIL
    assert preset.preferred_auth_mode == AuthMode.OAUTH
    assert preset.imap_host == "imap.gmail.com"


def test_apply_provider_preset_to_mailbox() -> None:
    mailbox = MailboxConfig(name="gmail-main", username="user@gmail.com")
    applied = apply_provider_preset(mailbox, "gmail")
    assert applied.provider == "gmail"
    assert applied.host == "imap.gmail.com"
    assert applied.port == 993
    assert applied.use_ssl is True


def test_supported_providers_contains_expected_set() -> None:
    providers = set(supported_providers())
    assert providers == {"gmail", "yandex", "mailru", "icloud"}


def run_tests() -> None:
    tests = [
        test_get_provider_preset_gmail,
        test_apply_provider_preset_to_mailbox,
        test_supported_providers_contains_expected_set,
    ]
    for test in tests:
        test()
    print(f"ok: {len(tests)} provider preset tests passed")


if __name__ == "__main__":
    run_tests()
