from __future__ import annotations

from dataclasses import dataclass, field

from config import MailboxConfig


@dataclass(slots=True)
class ValidationIssue:
    level: str
    field: str
    message: str


@dataclass(slots=True)
class ValidationReport:
    mailbox_name: str
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(issue.level == "error" for issue in self.issues)


def validate_mailbox_config(mailbox: MailboxConfig) -> ValidationReport:
    report = ValidationReport(mailbox_name=mailbox.name)

    if not mailbox.name:
        report.issues.append(ValidationIssue("error", "name", "Mailbox name is required"))
    if mailbox.provider not in {"imap"}:
        report.issues.append(ValidationIssue("error", "provider", f"Unsupported provider: {mailbox.provider}"))
    if mailbox.enabled:
        if not mailbox.host:
            report.issues.append(ValidationIssue("error", "host", "Host is required for enabled mailbox"))
        if not mailbox.username:
            report.issues.append(ValidationIssue("error", "username", "Username is required for enabled mailbox"))
    if mailbox.port is not None and mailbox.port <= 0:
        report.issues.append(ValidationIssue("error", "port", "Port must be > 0"))
    if not mailbox.folder:
        report.issues.append(ValidationIssue("warn", "folder", "Folder is empty; INBOX is usually expected"))

    return report
