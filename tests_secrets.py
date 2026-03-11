import os

from secrets_config import MailboxSecrets


def test_resolve_secret_from_env() -> None:
    os.environ["TEST_MAIL_SECRET"] = "secret-value"
    secrets = MailboxSecrets(password_env="TEST_MAIL_SECRET")
    assert secrets.resolve_secret() == "secret-value"
    del os.environ["TEST_MAIL_SECRET"]


def run_tests() -> None:
    tests = [test_resolve_secret_from_env]
    for test in tests:
        test()
    print(f"ok: {len(tests)} secrets tests passed")


if __name__ == "__main__":
    run_tests()
