import pytest

from mid.cli import SUBCOMMANDS, build_parser, main
from mid.config import Settings


def test_help_lists_subcommands(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--help"])
    assert exit_info.value.code == 0
    output = capsys.readouterr().out
    for name in SUBCOMMANDS:
        assert name in output


def test_subcommands_are_registered() -> None:
    parsed = build_parser().parse_args(["generate"])
    assert parsed.command == "generate"


def test_settings_defaults() -> None:
    settings = Settings()
    assert settings.llm_backend == "mock"
    assert settings.max_narrator_retries == 1


def test_settings_reject_unknown_backend() -> None:
    with pytest.raises(ValueError):
        Settings(llm_backend="openai")


def test_settings_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MID_LLM_BACKEND", "foundry")
    monkeypatch.setenv("MID_REPLAY_SPEED", "4")
    settings = Settings.from_env()
    assert settings.llm_backend == "foundry"
    assert settings.replay_speed == 4.0
