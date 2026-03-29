from __future__ import annotations

import json
import subprocess
from pathlib import Path

from gmail_oauth_backend import GmailOAuthBackend


def test_oauth_cli_lists_and_inspects_session() -> None:
    backend = GmailOAuthBackend(Path(".state/email_sanitizer/oauth_sessions.json"), secrets_path=Path(".state/email_sanitizer/oauth_secrets.json"))
    session, _ = backend.start(user_id="oauth-cli-user", mailbox_id="mbx_oauth_cli", mailbox_label="OAuth CLI")

    cli_path = Path(__file__).with_name("oauth_cli.py")
    list_out = subprocess.check_output(["python", str(cli_path), "list"], text=True)
    list_data = json.loads(list_out)
    assert any(item["auth_session_id"] == session.auth_session_id for item in list_data)

    session_out = subprocess.check_output([
        "python", str(cli_path), "session", "--auth-session-id", session.auth_session_id
    ], text=True)
    session_data = json.loads(session_out)
    assert session_data["status"] == "AUTH_URL_ISSUED"
    assert session_data["safe_summary"]


def run_tests() -> None:
    tests = [test_oauth_cli_lists_and_inspects_session]
    for test in tests:
        test()
    print(f"ok: {len(tests)} oauth cli tests passed")


if __name__ == "__main__":
    run_tests()
