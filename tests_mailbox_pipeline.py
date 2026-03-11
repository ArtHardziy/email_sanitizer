from config import MailboxConfig
from importance_classifier import ImportanceLevel, ImportancePolicy
from mail_fetcher import StaticMailFetcher, build_record
from mailbox_rules import SenderDomainRules
from pipeline import run_mailbox_pipeline
from policy_profiles import balanced_policy


def test_denied_domain_suppresses_notification() -> None:
    mailbox = MailboxConfig(
        name="personal",
        host="imap.example.com",
        username="user@example.com",
        policy=balanced_policy(),
        importance_policy=ImportancePolicy(priority_domains={"marketing.example.com"}),
        notify_min_level=ImportanceLevel.HIGH,
    )
    rules = SenderDomainRules(deny_domains={"marketing.example.com"})
    fetcher = StaticMailFetcher(
        records=[
            build_record(
                source_id="1",
                sender="newsletter@marketing.example.com",
                subject="Big sale",
                date="2026-03-11T16:00:00Z",
                body_text="Buy now. View in browser. Unsubscribe.",
            )
        ]
    )

    result = run_mailbox_pipeline(fetcher.fetch(), mailbox, rules)
    assert len(result.notifications) == 0


def test_priority_domain_notifies() -> None:
    mailbox = MailboxConfig(
        name="personal",
        host="imap.example.com",
        username="user@example.com",
        policy=balanced_policy(),
        importance_policy=ImportancePolicy(priority_domains={"github.com"}),
        notify_min_level=ImportanceLevel.HIGH,
    )
    fetcher = StaticMailFetcher(
        records=[
            build_record(
                source_id="2",
                sender="alerts@github.com",
                subject="Review requested",
                date="2026-03-11T16:05:00Z",
                body_text="A regular code review request for your repository.",
            )
        ]
    )

    result = run_mailbox_pipeline(fetcher.fetch(), mailbox)
    assert len(result.notifications) == 1
    assert "github.com" in result.notifications[0].title


def run_tests() -> None:
    tests = [
        test_denied_domain_suppresses_notification,
        test_priority_domain_notifies,
    ]
    for test in tests:
        test()
    print(f"ok: {len(tests)} mailbox pipeline tests passed")


if __name__ == "__main__":
    run_tests()
