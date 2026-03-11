from pathlib import Path

from config_loader import load_app_config
from importance_classifier import ImportanceLevel


def test_load_sample_config() -> None:
    path = Path(__file__).with_name("sample_config.json")
    config = load_app_config(path)

    assert len(config.mailboxes) == 1
    mailbox = config.mailboxes[0]
    assert mailbox.name == "personal"
    assert mailbox.notify_min_level == ImportanceLevel.HIGH
    assert "github.com" in mailbox.importance_policy.priority_domains


def run_tests() -> None:
    tests = [test_load_sample_config]
    for test in tests:
        test()
    print(f"ok: {len(tests)} config tests passed")


if __name__ == "__main__":
    run_tests()
