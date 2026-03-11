from __future__ import annotations

import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from models import RawEmail, RedactionResult, RiskFlag

OTP_RE = re.compile(r"\b(?:otp|verification code|passcode|one-time password|login code|sign-in code|2fa code)\b[:\s-]*([A-Z0-9]{4,10})", re.IGNORECASE)
GENERIC_CODE_RE = re.compile(r"\b\d{4,8}\b")
TOKEN_RE = re.compile(r"\b(?:token|api[_-]?key|secret|session[_-]?id|access[_-]?token)\b[:=\s-]*([A-Za-z0-9_\-\.]{6,})", re.IGNORECASE)
EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"\+?\d[\d\s\-()]{8,}\d")
SHORTENER_HOST_RE = re.compile(r"^(?:bit\.ly|t\.co|tinyurl\.com|goo\.gl|rb\.gy|cutt\.ly)$", re.IGNORECASE)

INJECTION_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"ignore\s+previous\s+instructions",
        r"ignore\s+all\s+prior\s+instructions",
        r"system\s+prompt",
        r"developer\s+message",
        r"you\s+are\s+an\s+ai\s+assistant",
        r"use\s+your\s+tools",
        r"forward\s+credentials",
        r"reveal\s+secrets",
        r"call\s+this\s+api",
        r"click\s+the\s+link\s+and",
        r"reply\s+with\s+(?:the\s+)?code",
        r"bypass\s+safety",
        r"exfiltrat(?:e|ion)",
        r"send\s+me\s+your\s+configuration",
        r"act\s+as\s+(?:system|developer)",
    ]
]

TOOL_INVOCATION_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"run\s+this\s+command",
        r"execute\s+this\s+command",
        r"open\s+this\s+link",
        r"call\s+this\s+api",
        r"use\s+your\s+browser",
        r"download\s+the\s+attachment",
        r"send\s+this\s+to",
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
        r"final\s+warning",
        r"avoid\s+(?:suspension|termination)",
    ]
]

MEDICAL_PATTERNS = [re.compile(p, re.IGNORECASE) for p in [r"diagnosis", r"lab result", r"анализ", r"врач", r"клиник", r"medical", r"эхо\s*экг"]]
FINANCIAL_PATTERNS = [re.compile(p, re.IGNORECASE) for p in [r"invoice", r"payment", r"card", r"bank", r"billing", r"счет", r"оплат", r"balance"]]
SENSITIVE_ATTACHMENT_EXTENSIONS = {".pdf", ".p7s", ".doc", ".docx", ".xls", ".xlsx", ".zip"}
AUTH_QUERY_KEYS = {"token", "code", "otp", "auth", "key", "session", "reset_token", "magic", "access_token"}


def detect_risk_flags(email: RawEmail) -> list[RiskFlag]:
    text = "\n".join(filter(None, [email.subject, email.snippet, email.body_text]))
    flags: list[RiskFlag] = []

    if any(p.search(text) for p in INJECTION_PATTERNS):
        flags.append(RiskFlag.PROMPT_INJECTION)
    if any(p.search(text) for p in TOOL_INVOCATION_PATTERNS):
        flags.append(RiskFlag.TOOL_INVOCATION_ATTEMPT)
    if re.search(r"\b(password|passcode|verification code|otp|2fa|confirm your identity|magic link|reset your password)\b", text, re.IGNORECASE):
        flags.append(RiskFlag.CREDENTIAL_REQUEST)
    if OTP_RE.search(text) or _looks_like_standalone_auth_code(text):
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
    if _contains_suspicious_url(text):
        flags.append(RiskFlag.SUSPICIOUS_URL)
    return list(dict.fromkeys(flags))


def sanitize_text(text: str, *, redact_contact_details: bool = False) -> RedactionResult:
    redactions: list[str] = []
    removed_instruction_spans = 0

    def replace_and_mark(pattern: re.Pattern[str], replacement: str, label: str, source: str) -> str:
        new_text, count = pattern.subn(replacement, source)
        if count:
            redactions.append(f"{label}:{count}")
        return new_text

    sanitized = text
    sanitized = replace_and_mark(OTP_RE, "[REDACTED_OTP]", "otp", sanitized)
    sanitized = replace_and_mark(TOKEN_RE, "[REDACTED_TOKEN]", "token", sanitized)

    if _looks_like_standalone_auth_code(sanitized):
        sanitized = GENERIC_CODE_RE.sub("[REDACTED_CODE]", sanitized, count=1)
        redactions.append("generic_code:1")

    for pattern in INJECTION_PATTERNS + TOOL_INVOCATION_PATTERNS:
        sanitized, count = pattern.subn("[UNTRUSTED_INSTRUCTION_REMOVED]", sanitized)
        removed_instruction_spans += count
        if count:
            redactions.append(f"instruction_removed:{count}")

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
            host = parsed.netloc.lower()
            if SHORTENER_HOST_RE.search(host):
                redactions.append("shortener_url:1")
                return f"{parsed.scheme}://{parsed.netloc}/[REDACTED_SHORT_LINK]"
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


def _contains_suspicious_url(text: str) -> bool:
    for url in re.findall(r"https?://[^\s)]+", text, re.IGNORECASE):
        try:
            parsed = urlparse(url)
            if SHORTENER_HOST_RE.search(parsed.netloc.lower()):
                return True
        except Exception:
            return True
    return False


def _looks_like_standalone_auth_code(text: str) -> bool:
    return bool(re.search(r"(?:verification|confirm|login|sign-in|signin|2fa|otp)[^\n]{0,40}\b\d{4,8}\b", text, re.IGNORECASE))


def _attachment_looks_sensitive(filename: str) -> bool:
    lower = filename.lower()
    return any(lower.endswith(ext) for ext in SENSITIVE_ATTACHMENT_EXTENSIONS)
