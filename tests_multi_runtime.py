from __future__ import annotations

import tempfile
from pathlib import Path

from multi_runtime_loader import load_multi_runtime


def test_load_multi_runtime_with_two_mailboxes() -> None:
    config_path = Path(__file__).with_name("multi_mailbox_config_sample.json")
    with tempfile.TemporaryDirectory() as tmp:
        runtime = load_multi_runtime(user_id="user-1", config_path=config_path, state_dir=tmp)
        assert runtime.user_id == "user-1"
        assert len(runtime.mailboxes) == 2
        assert runtime.get_mailbox("gmail-main") is not None
        assert runtime.get_mailbox("yandex-main") is not None
        assert runtime.mailbox_names() == ["gmail-main", "yandex-main"]


def run_tests() -> None:
    tests = [test_load_multi_runtime_with_two_mailboxes]
    for test in tests:
        test()
    print(f"ok: {len(tests)} multi-runtime tests passed")


if __name__ == "__main__":
    run_tests()
