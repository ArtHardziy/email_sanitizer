from __future__ import annotations

import json
from dataclasses import asdict

from gmail_oauth_service import start_google_oauth


if __name__ == "__main__":
    session, start = start_google_oauth(user_id="demo-user", mailbox_label="Primary Gmail")
    print(json.dumps({
        "authSession": asdict(session),
        "start": asdict(start),
    }, ensure_ascii=False))
