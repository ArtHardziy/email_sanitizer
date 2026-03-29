from __future__ import annotations

import json
import subprocess
from pathlib import Path

from onboarding_service import complete_auth, connect_mailbox


def test_onboarding_cli_status_outputs_health_and_credential_ref() -> None:
    connected = connect_mailbox(user_id="user-1", provider="gmail", email_address="user@gmail.com")
    assert connected.auth_session is not None
    completed = complete_auth(
        mailbox=connected.mailbox,
        provider="gmail",
        auth_session_id=connected.auth_session.auth_session_id,
        state_token=connected.auth_session.state_token,
        authorization_code="code-123",
    )

    cli_path = Path(__file__).with_name("onboarding_cli.py")
    out = subprocess.check_output([
        "python",
        str(cli_path),
        "status",
        "--mailbox-id",
        connected.mailbox.mailbox_id,
    ], text=True)
    data = json.loads(out)
    assert data["health"]["health_status"] == "healthy"
    assert data["credential_ref"]["credential_ref_id"] == completed.credential_ref.credential_ref_id


def run_tests() -> None:
    tests = [test_onboarding_cli_status_outputs_health_and_credential_ref]
    for test in tests:
        test()
    print(f"ok: {len(tests)} onboarding cli status tests passed")


if __name__ == "__main__":
    run_tests()
