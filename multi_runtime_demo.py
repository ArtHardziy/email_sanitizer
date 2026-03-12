from __future__ import annotations

import json
import tempfile
from pathlib import Path

from multi_runtime_loader import load_multi_runtime


if __name__ == "__main__":
    config_path = Path(__file__).with_name("multi_mailbox_config_sample.json")
    with tempfile.TemporaryDirectory() as tmp:
        runtime = load_multi_runtime(user_id="demo-user", config_path=config_path, state_dir=tmp)
        print(json.dumps({
            "userId": runtime.user_id,
            "mailboxCount": len(runtime.mailboxes),
            "enabledMailboxes": [mb.mailbox.name for mb in runtime.enabled_mailboxes()],
        }, ensure_ascii=False))
