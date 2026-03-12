from __future__ import annotations

import os
from pathlib import Path
import tempfile

from runtime_loader import load_runtimes_from_config


def test_runtime_loader_applies_env_overrides() -> None:
    os.environ["EMAIL_SANITIZER_PERSONAL_HOST"] = "imap.env.example.com"
    path = Path(__file__).with_name("sample_config.json")
    with tempfile.TemporaryDirectory() as tmp:
        runtimes = load_runtimes_from_config(path, state_dir=tmp)
        assert runtimes[0].mailbox.host == "imap.env.example.com"
    del os.environ["EMAIL_SANITIZER_PERSONAL_HOST"]


def run_tests() -> None:
    tests = [test_runtime_loader_applies_env_overrides]
    for test in tests:
        test()
    print(f"ok: {len(tests)} live runtime env tests passed")


if __name__ == "__main__":
    run_tests()
