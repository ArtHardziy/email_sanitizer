from pathlib import Path
import tempfile

from runtime_loader import load_runtimes_from_config


def test_load_runtimes_from_sample_config() -> None:
    path = Path(__file__).with_name("sample_config.json")
    with tempfile.TemporaryDirectory() as tmp:
        runtimes = load_runtimes_from_config(path, state_dir=tmp)
        assert len(runtimes) == 1
        assert runtimes[0].mailbox.name == "personal"


def run_tests() -> None:
    tests = [test_load_runtimes_from_sample_config]
    for test in tests:
        test()
    print(f"ok: {len(tests)} runtime loader tests passed")


if __name__ == "__main__":
    run_tests()
