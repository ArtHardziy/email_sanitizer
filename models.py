from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AllowedView(str, Enum):
    ALLOW_FULL = "allow_full"
    ALLOW_SANITIZED = "allow_sanitized"
    METADATA_ONLY = "metadata_only"
    SUMMARY_ONLY = "summary_only"
    BLOCK_AND_NOTIFY = "block_and_notify"


class RiskFlag(str, Enum):
    PROMPT_INJECTION = "prompt_injection"
    TOOL_INVOCATION_ATTEMPT = "tool_invocation_attempt"
    CREDENTIAL_REQUEST = "credential_request"
    OTP_PRESENT = "otp_present"
    AUTH_LINK_PRESENT = "auth_link_present"
    TOKEN_PRESENT = "token_present"
    SENSITIVE_ATTACHMENT = "sensitive_attachment"
    SENSITIVE_PII = "sensitive_pii"
    SOCIAL_ENGINEERING_TONE = "social_engineering_tone"
    UNEXPECTED_URGENCY = "unexpected_urgency"
    SUSPICIOUS_URL = "suspicious_url"
    MEDICAL_CONTENT = "medical_content"
    FINANCIAL_CONTENT = "financial_content"


@dataclass(slots=True)
class AttachmentMeta:
    filename: str
    mime_type: str
    size_bytes: int = 0


@dataclass(slots=True)
class RawEmail:
    sender: str
    subject: str
    date: str
    body_text: str
    snippet: Optional[str] = None
    attachments: List[AttachmentMeta] = field(default_factory=list)


@dataclass(slots=True)
class RedactionResult:
    sanitized_text: str
    redactions: List[str] = field(default_factory=list)
    removed_instruction_spans: int = 0


@dataclass(slots=True)
class SanitizedEmail:
    sender: str
    subject: str
    date: str
    risk_level: RiskLevel
    allowed_view: AllowedView
    risk_flags: List[RiskFlag] = field(default_factory=list)
    safe_summary: str = ""
    sanitized_snippet: Optional[str] = None
    sanitized_body: Optional[str] = None
    rationale: List[str] = field(default_factory=list)
    is_untrusted: bool = True
    instructions_removed: bool = False
    safe_for_agent: bool = False


@dataclass(slots=True)
class SanitizerPolicy:
    block_medical_content: bool = True
    block_financial_content: bool = True
    block_sensitive_attachments: bool = True
    redact_contact_details: bool = False
    allow_sanitized_work_emails: bool = True
    allow_sanitized_service_notifications: bool = True
    max_snippet_chars: int = 300
