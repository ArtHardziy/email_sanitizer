from __future__ import annotations

import json
import subprocess
from pathlib import Path

from delivery_format import render_plaintext, to_delivery_payload
from importance_classifier import ImportanceLevel
from notifier import NotificationMessage


def test_delivery_payload_and_plaintext() -> None:
    message = NotificationMessage(title="⚠️ Alert", body="Something happened", importance=ImportanceLevel.HIGH)
    payload = to_delivery_payload(message)
    assert payload.importance == "high"
    assert "Something happened" in render_plaintext(message)


def test_cli_validate_json() -> None:
    cli_path = Path(__file__).with_name("cli.py")
    config_path = Path(__file__).with_name("sample_config.json")
    out = subprocess.check_output(["python", str(cli_path), "validate", "--config", str(config_path), "--json"], text=True)
    data = json.loads(out)
    assert isinstance(data, list)
    assert data[0]["mailbox"] == "personal"


def test_cli_diagnose_json_contains_runtime_and_onboarding() -> None:
    cli_path = Path(__file__).with_name("cli.py")
    config_path = Path(__file__).with_name("sample_config.json")
    out = subprocess.check_output(["python", str(cli_path), "diagnose", "--config", str(config_path), "--json"], text=True)
    data = json.loads(out)
    assert isinstance(data, list)
    assert "runtime" in data[0]
    assert "onboarding" in data[0]


def run_tests() -> None:
    tests = [test_delivery_payload_and_plaintext, test_cli_validate_json, test_cli_diagnose_json_contains_runtime_and_onboarding]
    for test in tests:
        test()
    print(f"ok: {len(tests)} delivery/cli tests passed")


if __name__ == "__main__":
    run_tests()
