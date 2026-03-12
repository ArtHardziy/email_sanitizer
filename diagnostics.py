from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from runtime_config import MailboxRuntime
from secret_binding import bind_mailbox_secret
from validation import validate_mailbox_config


@dataclass(slots=True)
class RuntimeDiagnostic:
    mailbox_name: str
    provider: str
    enabled: bool
    config_ok: bool
    secret_resolved: bool
    issue_count: int


def diagnose_runtime(runtime: MailboxRuntime) -> RuntimeDiagnostic:
    report = validate_mailbox_config(runtime.mailbox)
    bound = bind_mailbox_secret(runtime.mailbox, runtime.secrets)
    return RuntimeDiagnostic(
        mailbox_name=runtime.mailbox.name,
        provider=runtime.mailbox.provider,
        enabled=runtime.mailbox.enabled,
        config_ok=report.ok,
        secret_resolved=bound.resolved_secret is not None,
        issue_count=len(report.issues),
    )


def diagnostic_to_json(diag: RuntimeDiagnostic) -> str:
    return json.dumps(asdict(diag), ensure_ascii=False)
