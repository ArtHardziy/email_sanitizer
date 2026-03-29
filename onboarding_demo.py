from __future__ import annotations

import copy
import json
from dataclasses import asdict

from onboarding_service import complete_auth, connect_mailbox


if __name__ == "__main__":
    connected = connect_mailbox(user_id="demo-user", provider="gmail", email_address="user@gmail.com")
    connect_snapshot = copy.deepcopy(asdict(connected))
    assert connected.auth_session is not None
    completed = complete_auth(
        mailbox=connected.mailbox,
        provider="gmail",
        auth_session_id=connected.auth_session.auth_session_id,
        state_token=connected.auth_session.state_token,
        authorization_code="demo-code",
    )
    print(json.dumps({
        "connect": connect_snapshot,
        "complete": asdict(completed),
    }, ensure_ascii=False))
