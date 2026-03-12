from __future__ import annotations

import copy
import json
from dataclasses import asdict

from onboarding_service import complete_auth, connect_mailbox


if __name__ == "__main__":
    connected = connect_mailbox(user_id="demo-user", provider="gmail", email_address="user@gmail.com")
    connect_snapshot = copy.deepcopy(asdict(connected))
    completed = complete_auth(mailbox=connected.mailbox, provider="gmail")
    print(json.dumps({
        "connect": connect_snapshot,
        "complete": asdict(completed),
    }, ensure_ascii=False))
