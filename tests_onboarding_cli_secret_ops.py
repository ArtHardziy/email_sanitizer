from __future__ import annotations

import json
import subprocess
from pathlib import Path


def test_onboarding_cli_revoke_rotate_and_reauth_start() -> None:
    cli_path = Path(__file__).with_name("onboarding_cli.py")

    connect_out = subprocess.check_output([
        "python", str(cli_path), "connect", "gmail",
        "--user-id", "user-secret-ops", "--email", "user@gmail.com", "--display-name", "Primary Gmail",
    ], text=True)
    connect_data = json.loads(connect_out)
    mailbox_id = connect_data["mailbox"]["mailbox_id"]
    auth_session_id = connect_data["auth_session"]["auth_session_id"]
    state_token = connect_data["auth_session"]["state_token"]

    subprocess.check_output([
        "python", str(cli_path), "auth-complete", "gmail",
        "--user-id", "user-secret-ops", "--mailbox-id", mailbox_id,
        "--email", "user@gmail.com", "--display-name", "Primary Gmail",
        "--auth-session-id", auth_session_id, "--state-token", state_token, "--authorization-code", "demo-code",
    ], text=True)

    revoke_out = subprocess.check_output([
        "python", str(cli_path), "revoke-secret", "--mailbox-id", mailbox_id,
    ], text=True)
    revoke_data = json.loads(revoke_out)
    assert revoke_data["status"] == "REVOKED"

    reauth_out = subprocess.check_output([
        "python", str(cli_path), "reauth-start", "--mailbox-id", mailbox_id,
    ], text=True)
    reauth_data = json.loads(reauth_out)
    assert reauth_data["auth_session"] is not None
    assert reauth_data["mailbox"]["mailbox_id"] == mailbox_id
    assert reauth_data["auth_session"]["mailbox_id"] == mailbox_id

    rotate_out = subprocess.check_output([
        "python", str(cli_path), "rotate-secret", "--mailbox-id", mailbox_id, "--new-secret-value", "manually-rotated-secret",
    ], text=True)
    rotate_data = json.loads(rotate_out)
    assert rotate_data["status"] == "ACTIVE"


def run_tests() -> None:
    tests = [test_onboarding_cli_revoke_rotate_and_reauth_start]
    for test in tests:
        test()
    print(f"ok: {len(tests)} onboarding cli secret ops tests passed")


if __name__ == "__main__":
    run_tests()
