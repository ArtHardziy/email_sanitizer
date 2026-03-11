from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class SenderDomainRules:
    allow_senders: set[str] = field(default_factory=set)
    allow_domains: set[str] = field(default_factory=set)
    deny_senders: set[str] = field(default_factory=set)
    deny_domains: set[str] = field(default_factory=set)

    def is_denied(self, sender: str) -> bool:
        sender_l = sender.lower()
        domain = sender_l.split("@", 1)[1] if "@" in sender_l else ""
        return sender_l in self.deny_senders or domain in self.deny_domains

    def is_explicitly_allowed(self, sender: str) -> bool:
        sender_l = sender.lower()
        domain = sender_l.split("@", 1)[1] if "@" in sender_l else ""
        return sender_l in self.allow_senders or domain in self.allow_domains
