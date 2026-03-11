from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class MailboxSecrets:
    password_env: Optional[str] = None
    app_password_env: Optional[str] = None
    oauth_token_env: Optional[str] = None

    def resolve_secret(self) -> str | None:
        for key in [self.password_env, self.app_password_env, self.oauth_token_env]:
            if key and os.environ.get(key):
                return os.environ[key]
        return None
