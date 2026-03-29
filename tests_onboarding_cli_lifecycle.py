from __future__ import annotations

import json
import subprocess
from pathlib import Path


def test_onboarding_cli_list_and_status_work_with_persisted_mailbox() -> None:
    cli_path = Path(__file__).with_name("onboarding_cli.py")

    connect_out = subprocess.check_output([
        "python",
        str(cli_path),
        "connect",
        "gmail",
        "--user-id",
        "user-cli-1",
        "--email",
        "user@gmail.com",
        "--display-name",
        "Primary Gmail",
    ], text=True)
    connect_data = json.loads(connect_out)
    mailbox_id = connect_data["mailbox"]["mailbox_id"]
    auth_session_id = connect_data["auth_session"]["auth_session_id"]
    state_token = connect_data["auth_session"]["state_token"]

    complete_out = subprocess.check_output([
        "python",
        str(cli_path),
        "auth-complete",
        "gmail",
        "--user-id",
        "user-cli-1",
        "--mailbox-id",
        mailbox_id,
        "--email",
        "user@gmail.com",
        "--display-name",
        "Primary Gmail",
        "--auth-session-id",
        auth_session_id,
        "--state-token",
        state_token,
        "--authorization-code",
        "demo-code",
    ], text=True)
    complete_data = json.loads(complete_out)
    assert complete_data["mailbox"]["state"] == "ACTIVE"

    status_out = subprocess.check_output([
        "python",
        str(cli_path),
        "status",
        "--mailbox-id",
        mailbox_id,
    ], text=True)
    status_data = json.loads(status_out)
    assert status_data["mailbox"]["mailbox_id"] == mailbox_id
    assert status_data["health"]["health_status"] == "healthy"

    list_out = subprocess.check_output([
        "python",
        str(cli_path),
        "list",
        "--user-id",
        "user-cli-1",
    ], text=True)
    list_data = json.loads(list_out)
    assert any(item["mailbox_id"] == mailbox_id for item in list_data)


def run_tests() -> None:
    tests = [test_onboarding_cli_list_and_status_work_with_persisted_mailbox]
    for test in tests:
        test()
    print(f"ok: {len(tests)} onboarding cli lifecycle tests passed")


if __name__ == "__main__":
    run_tests()
