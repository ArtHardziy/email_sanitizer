from extractors import extract_facts
from html_utils import html_to_text


def test_html_to_text_removes_tags() -> None:
    value = "<html><body><h1>Hello</h1><script>alert(1)</script><p>World</p></body></html>"
    text = html_to_text(value)
    assert text == "Hello World"


def test_extract_facts_finds_actions_and_dates() -> None:
    text = "Please review the document today. Call the clinic at 14:30."
    facts = extract_facts(text)
    assert any("Please review" in item for item in facts.action_items)
    assert "today" in [item.lower() for item in facts.date_mentions]
    assert "14:30" in facts.date_mentions


def run_tests() -> None:
    tests = [test_html_to_text_removes_tags, test_extract_facts_finds_actions_and_dates]
    for test in tests:
        test()
    print(f"ok: {len(tests)} html/extractor tests passed")


if __name__ == "__main__":
    run_tests()
