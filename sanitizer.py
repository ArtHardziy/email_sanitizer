from __future__ import annotations

from models import AllowedView, RawEmail, RiskFlag, RiskLevel, SanitizedEmail, SanitizerPolicy
from rules import detect_risk_flags, sanitize_text
from summary_builder import build_content_aware_summary


CRITICAL_FLAGS = {
    RiskFlag.PROMPT_INJECTION,
    RiskFlag.TOOL_INVOCATION_ATTEMPT,
    RiskFlag.OTP_PRESENT,
    RiskFlag.AUTH_LINK_PRESENT,
    RiskFlag.TOKEN_PRESENT,
}

HIGH_FLAGS = {
    RiskFlag.CREDENTIAL_REQUEST,
    RiskFlag.SENSITIVE_ATTACHMENT,
    RiskFlag.SOCIAL_ENGINEERING_TONE,
    RiskFlag.MEDICAL_CONTENT,
    RiskFlag.FINANCIAL_CONTENT,
    RiskFlag.SUSPICIOUS_URL,
}


def sanitize_email(email: RawEmail, policy: SanitizerPolicy | None = None) -> SanitizedEmail:
    policy = policy or SanitizerPolicy()
    flags = detect_risk_flags(email)
    combined_text = "\n".join(filter(None, [email.snippet, email.body_text]))
    redaction = sanitize_text(combined_text, redact_contact_details=policy.redact_contact_details)
    sanitized_snippet = (redaction.sanitized_text[: policy.max_snippet_chars]).strip() or None

    risk_level = _compute_risk_level(flags)
    allowed_view = _decide_allowed_view(flags, policy)
    summary = build_content_aware_summary(email, flags, allowed_view, redaction.sanitized_text)
    rationale = _build_rationale(flags, allowed_view, redaction.redactions)

    return SanitizedEmail(
        sender=email.sender,
        subject=email.subject,
        date=email.date,
        risk_level=risk_level,
        allowed_view=allowed_view,
        risk_flags=flags,
        safe_summary=summary,
        sanitized_snippet=sanitized_snippet if allowed_view in {AllowedView.ALLOW_SANITIZED, AllowedView.SUMMARY_ONLY} else None,
        sanitized_body=redaction.sanitized_text if allowed_view == AllowedView.ALLOW_SANITIZED else None,
        rationale=rationale,
        is_untrusted=True,
        instructions_removed=redaction.removed_instruction_spans > 0,
        safe_for_agent=allowed_view in {AllowedView.ALLOW_SANITIZED, AllowedView.SUMMARY_ONLY, AllowedView.METADATA_ONLY},
    )


def _compute_risk_level(flags: list[RiskFlag]) -> RiskLevel:
    if any(flag in CRITICAL_FLAGS for flag in flags):
        return RiskLevel.CRITICAL
    if any(flag in HIGH_FLAGS for flag in flags):
        return RiskLevel.HIGH
    if flags:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def _decide_allowed_view(flags: list[RiskFlag], policy: SanitizerPolicy) -> AllowedView:
    flag_set = set(flags)

    if flag_set & CRITICAL_FLAGS:
        return AllowedView.BLOCK_AND_NOTIFY
    if policy.block_sensitive_attachments and RiskFlag.SENSITIVE_ATTACHMENT in flag_set:
        return AllowedView.BLOCK_AND_NOTIFY
    if policy.block_medical_content and RiskFlag.MEDICAL_CONTENT in flag_set:
        return AllowedView.METADATA_ONLY
    if policy.block_financial_content and RiskFlag.FINANCIAL_CONTENT in flag_set:
        return AllowedView.METADATA_ONLY
    if flag_set:
        return AllowedView.SUMMARY_ONLY
    return AllowedView.ALLOW_SANITIZED


def _build_rationale(flags: list[RiskFlag], allowed_view: AllowedView, redactions: list[str]) -> list[str]:
    rationale = [f"allowed_view={allowed_view.value}"]
    if flags:
        rationale.append("risk_flags=" + ",".join(flag.value for flag in flags))
    if redactions:
        rationale.append("redactions=" + ",".join(redactions))
    return rationale
