from __future__ import annotations

from models import SanitizerPolicy


def strict_policy() -> SanitizerPolicy:
    return SanitizerPolicy(
        block_medical_content=True,
        block_financial_content=True,
        block_sensitive_attachments=True,
        redact_contact_details=True,
        allow_sanitized_work_emails=False,
        allow_sanitized_service_notifications=False,
        max_snippet_chars=180,
    )


def balanced_policy() -> SanitizerPolicy:
    return SanitizerPolicy(
        block_medical_content=True,
        block_financial_content=True,
        block_sensitive_attachments=True,
        redact_contact_details=False,
        allow_sanitized_work_emails=True,
        allow_sanitized_service_notifications=True,
        max_snippet_chars=300,
    )


def work_heavy_policy() -> SanitizerPolicy:
    return SanitizerPolicy(
        block_medical_content=True,
        block_financial_content=True,
        block_sensitive_attachments=True,
        redact_contact_details=False,
        allow_sanitized_work_emails=True,
        allow_sanitized_service_notifications=True,
        max_snippet_chars=500,
    )


def privacy_max_policy() -> SanitizerPolicy:
    return SanitizerPolicy(
        block_medical_content=True,
        block_financial_content=True,
        block_sensitive_attachments=True,
        redact_contact_details=True,
        allow_sanitized_work_emails=False,
        allow_sanitized_service_notifications=False,
        max_snippet_chars=120,
    )
