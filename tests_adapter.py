from imap_adapter import parse_eml_bytes


def test_parse_simple_eml_bytes() -> None:
    payload = b"From: alerts@example.com\nSubject: Test message\nDate: Wed, 11 Mar 2026 16:00:00 +0000\nContent-Type: text/plain; charset=utf-8\n\nHello from email body."
    record = parse_eml_bytes("eml:1", payload)

    assert record.source_id == "eml:1"
    assert record.raw_email.sender == "alerts@example.com"
    assert record.raw_email.subject == "Test message"
    assert "Hello from email body." in record.raw_email.body_text


def run_tests() -> None:
    tests = [test_parse_simple_eml_bytes]
    for test in tests:
        test()
    print(f"ok: {len(tests)} adapter tests passed")


if __name__ == "__main__":
    run_tests()
