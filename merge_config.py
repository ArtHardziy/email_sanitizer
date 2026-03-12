from __future__ import annotations

import os
from dataclasses import replace
from pathlib import Path
from typing import Any

from config import MailboxConfig
from secrets_config import MailboxSecrets


def merge_mailbox_with_env(mailbox: MailboxConfig, prefix: str | None = None) -> MailboxConfig:
    key = _env_prefix(mailbox.name, prefix)
    host = os.environ.get(f"{key}_HOST", mailbox.host)
    port = int(os.environ.get(f"{key}_PORT", mailbox.port or 0) or 0) or mailbox.port
    username = os.environ.get(f"{key}_USERNAME", mailbox.username)
    folder = os.environ.get(f"{key}_FOLDER", mailbox.folder)
    use_ssl = _env_bool(os.environ.get(f"{key}_USE_SSL"), mailbox.use_ssl)
    enabled = _env_bool(os.environ.get(f"{key}_ENABLED"), mailbox.enabled)
    return replace(
        mailbox,
        host=host,
        port=port,
        username=username,
        folder=folder,
        use_ssl=use_ssl,
        enabled=enabled,
    )


def secrets_from_env(mailbox_name: str, prefix: str | None = None) -> MailboxSecrets:
    key = _env_prefix(mailbox_name, prefix)
    return MailboxSecrets(
        password_env=f"{key}_PASSWORD",
        app_password_env=f"{key}_APP_PASSWORD",
        oauth_token_env=f"{key}_OAUTH_TOKEN",
    )


def _env_prefix(mailbox_name: str, prefix: str | None = None) -> str:
    base = prefix or "EMAIL_SANITIZER"
    normalized = mailbox_name.upper().replace("-", "_").replace(" ", "_")
    return f"{base}_{normalized}"


def _env_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}
