from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from credential_registry import CredentialRegistry
from mailbox_diagnostics import build_mailbox_diagnostic_bundle
from mailbox_registry import MailboxRegistry
from oauth_state_store import OAuthSessionStore
from runtime_config import MailboxRuntime
from secret_binding import bind_mailbox_secret
from secret_manager import LocalSecretManager
from validation import validate_mailbox_config


@dataclass(slots=True)
class RuntimeDiagnostic:
    mailbox_name: str
    provider: str
    enabled: bool
    config_ok: bool
    secret_resolved: bool
    issue_count: int


@dataclass(slots=True)
class OnboardingDiagnostic:
    mailbox_id: str
    provider: str
    mailbox_state: str
    provider_account_id: str | None
    credential_ref_id: str | None
    credential_provider_account_id: str | None
    client_secret_ref_id: str | None
    secret_ref_id: str | None
    secret_status: str | None
    health_status: str
    health_error_code: str | None
    remediation_hints: list[str]
    oauth_session_count: int
    oauth_pending_count: int
    oauth_expired_count: int
    oauth_failed_count: int


@dataclass(slots=True)
class CombinedDiagnostic:
    runtime: RuntimeDiagnostic
    onboarding: list[OnboardingDiagnostic]


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


def diagnose_onboarding_state(state_dir: str | Path = ".state/email_sanitizer") -> list[OnboardingDiagnostic]:
    state_path = Path(state_dir)
    mailboxes = MailboxRegistry(state_path / "mailboxes.json")
    credential_refs = CredentialRegistry(state_path / "credential_refs.json")
    oauth_sessions = OAuthSessionStore(state_path / "oauth_sessions.json")
    secret_manager = LocalSecretManager(state_path / "oauth_secrets.json")

    by_mailbox_id: dict[str, list] = {}
    for session in oauth_sessions.list_all():
        if session.mailbox_id:
            by_mailbox_id.setdefault(session.mailbox_id, []).append(session)

    diagnostics: list[OnboardingDiagnostic] = []
    for mailbox in mailboxes.list_all():
        credential_ref = credential_refs.get(mailbox.credential_ref_id) if mailbox.credential_ref_id else None
        secret_descriptor = None
        if credential_ref and credential_ref.secret_ref_id:
            try:
                secret_descriptor = secret_manager.describe_secret(credential_ref.secret_ref_id)
            except ValueError:
                secret_descriptor = None
        bundle = build_mailbox_diagnostic_bundle(
            mailbox,
            credential_ref,
            by_mailbox_id.get(mailbox.mailbox_id, []),
            secret_descriptor,
        )
        diagnostics.append(OnboardingDiagnostic(
            mailbox_id=bundle.mailbox_id,
            provider=bundle.provider,
            mailbox_state=bundle.mailbox_state,
            provider_account_id=bundle.provider_account_id,
            credential_ref_id=bundle.credential_ref_id,
            credential_provider_account_id=bundle.credential_provider_account_id,
            client_secret_ref_id=bundle.client_secret_ref_id,
            secret_ref_id=bundle.secret_ref_id,
            secret_status=bundle.secret_status,
            health_status=bundle.health_status,
            health_error_code=bundle.health_error_code,
            remediation_hints=bundle.remediation_hints,
            oauth_session_count=bundle.oauth_session_count,
            oauth_pending_count=bundle.oauth_pending_count,
            oauth_expired_count=bundle.oauth_expired_count,
            oauth_failed_count=bundle.oauth_failed_count,
        ))
    return diagnostics


def diagnose_combined(runtime: MailboxRuntime, state_dir: str | Path = ".state/email_sanitizer") -> CombinedDiagnostic:
    return CombinedDiagnostic(runtime=diagnose_runtime(runtime), onboarding=diagnose_onboarding_state(state_dir))


def diagnostic_to_json(diag: RuntimeDiagnostic) -> str:
    return json.dumps(asdict(diag), ensure_ascii=False)
