from config import MailboxConfig
from importance_classifier import ImportanceLevel, ImportancePolicy
from mail_fetcher import StaticMailFetcher, build_record
from mailbox_rules import SenderDomainRules
from pipeline import run_mailbox_pipeline
from policy_profiles import balanced_policy


if __name__ == "__main__":
    mailbox = MailboxConfig(
        name="personal",
        provider="imap",
        host="imap.example.com",
        username="user@example.com",
        policy=balanced_policy(),
        importance_policy=ImportancePolicy(priority_domains={"github.com", "clinic.example.com"}),
        notify_min_level=ImportanceLevel.HIGH,
    )
    rules = SenderDomainRules(deny_domains={"marketing.example.com"})

    fetcher = StaticMailFetcher(
        records=[
            build_record(
                source_id="1",
                sender="alerts@github.com",
                subject="Review requested",
                date="2026-03-11T16:05:00Z",
                body_text="A regular code review request for your repository.",
            ),
            build_record(
                source_id="2",
                sender="newsletter@marketing.example.com",
                subject="Weekly sale",
                date="2026-03-11T16:06:00Z",
                body_text="View in browser. Unsubscribe here. Buy now.",
            ),
        ]
    )

    result = run_mailbox_pipeline(fetcher.fetch(), mailbox, rules)
    for notification in result.notifications:
        print(notification)
