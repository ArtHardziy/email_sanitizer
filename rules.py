from __future__ import annotations

import re
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

from models import RawEmail, RedactionResult, RiskFlag

OTP_RE = re.compile(r"\b(?:code|otp|verification code|passcode|one-time password)\b[:\s-]*([A-Z0-9]{4,10})", re.IGNORECASE)
TOKEN_RE = re.compile(r"\b(?:token|api[_-]?key|secret|session[_-]?id|access[_-]?token)\b[:=\s-]*([A-Za-z0-9_\-\.]{6,})", re.IGNORECASE)
EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"\+?\d[\d\s\-()]{8,}\d")

INJECTION_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"ignore\s+previous\s+instructions",
        r"system\s+prompt",
        r"developer\s+message",
        r"you\s+are\s+an\s+ai\s+assistant",
        r"use\s+your\s+tools",
        r"forward\s+credentials",
        r"reveal\s+secrets",
        r"call\s+this\s+api",
        r"click\s+the\s+link\s+and",
        r"reply\s+with\s+(?:the\s+)?code",
    ]
]

SOCIAL_ENGINEERING_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"urgent(?:ly)?",
        r"act\s+now",
        r"immediately",
        r"account\s+(?:suspended|blocked|locked)",
        r"confirm\s+your\s+identity",
    ]
]

MEDICAL_PATTERNS = [re.compile(p, re.IGNORECASE) for p in [r"diagnosis", r"lab result", r"анализ", r"врач", r"клиник", r"medical"]]
FINANCIAL_PATTERNS = [re.compile(p, re.IGNORECASE) for p in [r"invoice", r"payment", r"card", r"bank", r"billing", r"счет", r"оплат"]]
SENSITIVE_ATTACHMENT_EXTENSIONS = {".pdf", ".p7s", ".doc", ".docx", ".xls", ".xlsx", ".zip"}
AUTH_QUERY_KEYS = {"token", "code", "otp", "auth", "key", "session", "reset_token", "magic", "access_token"}


def detect_risk_flags(email: RawEmail) -> list[RiskFlag]:
    text = "\n".join(filter(None, [email.subject, email.snippet, email.body_text]))
    flags: list[RiskFlag] = []

    if any(p.search(text) for p in INJECTION_PATTERNS):
        flags.append(RiskFlag.PROMPT_INJECTION)
    if re.search(r"\b(use your tools|call this api|open this link|run this command)\b", text, re.IGNORECASE):
        flags.append(RiskFlag.TOOL_INVOCATION_ATTEMPT)
    if re.search(r"\b(password|passcode|verification code|otp|2fa|confirm your identity)\b", text, re.IGNORECASE):
        flags.append(RiskFlag.CREDENTIAL_REQUEST)
    if OTP_RE.search(text):
        flags.append(RiskFlag.OTP_PRESENT)
    if TOKEN_RE.search(text):
        flags.append(RiskFlag.TOKEN_PRESENT)
    if any(p.search(text) for p in SOCIAL_ENGINEERING_PATTERNS):
        flags.append(RiskFlag.SOCIAL_ENGINEERING_TONE)
        flags.append(RiskFlag.UNEXPECTED_URGENCY)
    if any(p.search(text) for p in MEDICAL_PATTERNS):
        flags.append(RiskFlag.MEDICAL_CONTENT)
    if any(p.search(text) for p in FINANCIAL_PATTERNS):
        flags.append(RiskFlag.FINANCIAL_CONTENT)
    if any(_attachment_looks_sensitive(a.filename) for a in email.attachments):
        flags.append(RiskFlag.SENSITIVE_ATTACHMENT)
    if _contains_auth_link(text):
        flags.append(RiskFlag.AUTH_LINK_PRESENT)
    return list(dict.fromkeys(flags))


def sanitize_text(text: str, *, redact_contact_details: bool = False) -> RedactionResult:
    redactions: list[str] = []
    removed_instruction_spans = 0

    def replace_and_mark(pattern: re.Pattern[str], replacement: str, label: str, source: str) -> str:
        nonlocal redactions
        new_text, count = pattern.subn(replacement, source)
        if count:
            redactions.append(f"{label}:{count}")
        return new_text

    sanitized = text
    sanitized = replace_and_mark(OTP_RE, "[REDACTED_OTP]", "otp", sanitized)
    sanitized = replace_and_mark(TOKEN_RE, "[REDACTED_TOKEN]", "token", sanitized)

    for pattern in INJECTION_PATTERNS:
        sanitized, count = pattern.subn("[UNTRUSTED_INSTRUCTION_REMOVED]", sanitized)
        removed_instruction_spans += count
        if count:
            redactions.append(f"prompt_injection:{count}")

    sanitized = _sanitize_urls(sanitized, redactions)

    if redact_contact_details:
        sanitized = replace_and_mark(EMAIL_RE, "[REDACTED_EMAIL]", "email", sanitized)
        sanitized = replace_and_mark(PHONE_RE, "[REDACTED_PHONE]", "phone", sanitized)

    return RedactionResult(
        sanitized_text=sanitized.strip(),
        redactions=redactions,
        removed_instruction_spans=removed_instruction_spans,
    )


def _sanitize_urls(text: str, redactions: list[str]) -> str:
    url_re = re.compile(r"https?://[^\s)]+", re.IGNORECASE)

    def repl(match: re.Match[str]) -> str:
        raw = match.group(0)
        try:
            parsed = urlparse(raw)
            query = parse_qsl(parsed.query, keep_blank_values=True)
            filtered = []
            removed = False
            for key, value in query:
                if key.lower() in AUTH_QUERY_KEYS:
                    filtered.append((key, "[REDACTED]"))
                    removed = True
                else:
                    filtered.append((key, value))
            new_query = urlencode(filtered)
            rebuilt = urlunparse(parsed._replace(query=new_query))
            if removed:
                redactions.append("auth_query_params:1")
            return rebuilt
        except Exception:
            redactions.append("url_parse_error:1")
            return "[REDACTED_URL]"

    return url_re.sub(repl, text)


def _contains_auth_link(text: str) -> bool:
    for url in re.findall(r"https?://[^\s)]+", text, re.IGNORECASE):
        try:
            parsed = urlparse(url)
            for key, _ in parse_qsl(parsed.query, keep_blank_values=True):
                if key.lower() in AUTH_QUERY_KEYS:
                    return True
        except Exception:
            return True
    return False


def _attachment_looks_sensitive(filename: str) -> bool:
    lower = filename.lower()
    return any(lower.endswith(ext) for ext in SENSITIVE_ATTACHMENT_EXTENSIONS)
