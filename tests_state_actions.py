from pathlib import Path
import tempfile

from action_classifier import ActionKind, classify_actions
from state_store import JsonStateStore, MailState


def test_action_classifier_detects_reply_call_payment() -> None:
    text = "Please reply today. Позвонить в клинику в 14:30. Payment required before Friday."
    signals = classify_actions(text)

    assert ActionKind.REPLY_NEEDED in signals.kinds
    assert ActionKind.CALL_NEEDED in signals.kinds
    assert ActionKind.PAYMENT_NEEDED in signals.kinds


def test_state_store_roundtrip() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "state.json"
        store = JsonStateStore(path)
        state = store.load()
        assert state.processed_ids == set()

        store.mark_processed(state, ["a", "b"])
        loaded = store.load()
        assert loaded.processed_ids == {"a", "b"}


def run_tests() -> None:
    tests = [test_action_classifier_detects_reply_call_payment, test_state_store_roundtrip]
    for test in tests:
        test()
    print(f"ok: {len(tests)} state/action tests passed")


if __name__ == "__main__":
    run_tests()
