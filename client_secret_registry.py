from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from provider_presets import get_provider_preset
from secret_manager import LocalSecretManager


@dataclass(slots=True)
class ClientSecretValidationResult:
    provider: str
    client_id: str | None
    client_secret_ref_id: str | None
    token_endpoint_auth_method: str | None
    ok: bool
    safe_message: str


def validate_provider_client_secret_ref(provider: str) -> ClientSecretValidationResult:
    preset = get_provider_preset(provider)
    oauth_config = preset.oauth_config
    client_config = oauth_config.client_config if oauth_config else None

    if not oauth_config or not client_config:
        return ClientSecretValidationResult(
            provider=provider,
            client_id=None,
            client_secret_ref_id=None,
            token_endpoint_auth_method=None,
            ok=False,
            safe_message="Provider OAuth client config is missing.",
        )

    if not client_config.client_id:
        return ClientSecretValidationResult(
            provider=provider,
            client_id=None,
            client_secret_ref_id=client_config.client_secret_ref_id,
            token_endpoint_auth_method=client_config.token_endpoint_auth_method,
            ok=False,
            safe_message="OAuth client_id metadata is missing.",
        )

    if not client_config.client_secret_ref_id:
        return ClientSecretValidationResult(
            provider=provider,
            client_id=client_config.client_id,
            client_secret_ref_id=None,
            token_endpoint_auth_method=client_config.token_endpoint_auth_method,
            ok=False,
            safe_message="OAuth client secret ref metadata is missing.",
        )

    return ClientSecretValidationResult(
        provider=provider,
        client_id=client_config.client_id,
        client_secret_ref_id=client_config.client_secret_ref_id,
        token_endpoint_auth_method=client_config.token_endpoint_auth_method,
        ok=True,
        safe_message="OAuth client metadata is present.",
    )


def validate_provider_client_secret_runtime(
    provider: str,
    *,
    secrets_path: str | Path = ".state/email_sanitizer/oauth_secrets.json",
) -> ClientSecretValidationResult:
    base = validate_provider_client_secret_ref(provider)
    if not base.ok or not base.client_secret_ref_id:
        return base

    manager = LocalSecretManager(secrets_path)
    try:
        descriptor = manager.describe_secret(base.client_secret_ref_id)
    except ValueError:
        return ClientSecretValidationResult(
            provider=base.provider,
            client_id=base.client_id,
            client_secret_ref_id=base.client_secret_ref_id,
            token_endpoint_auth_method=base.token_endpoint_auth_method,
            ok=False,
            safe_message="OAuth client secret ref is configured but missing in secret storage.",
        )

    if descriptor.status != "ACTIVE":
        return ClientSecretValidationResult(
            provider=base.provider,
            client_id=base.client_id,
            client_secret_ref_id=base.client_secret_ref_id,
            token_endpoint_auth_method=base.token_endpoint_auth_method,
            ok=False,
            safe_message="OAuth client secret ref exists but is not active.",
        )

    return ClientSecretValidationResult(
        provider=base.provider,
        client_id=base.client_id,
        client_secret_ref_id=base.client_secret_ref_id,
        token_endpoint_auth_method=base.token_endpoint_auth_method,
        ok=True,
        safe_message="OAuth client metadata and secret ref are present.",
    )
