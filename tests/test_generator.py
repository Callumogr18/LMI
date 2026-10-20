from pathlib import Path

import pytest

from mid.cli import main
from mid.generator import generate_match, read_match, write_match
from mid.models import Event, EventType, Outcome

SEEDS = (1, 2, 3)


@pytest.mark.parametrize("seed", SEEDS)
def test_same_seed_produces_identical_events(seed: int) -> None:
    assert generate_match(seed) == generate_match(seed)


def test_same_seed_produces_identical_file_bytes(tmp_path: Path) -> None:
    first, second = tmp_path / "a.jsonl", tmp_path / "b.jsonl"
    write_match(generate_match(1), first)
    write_match(generate_match(1), second)
    assert first.read_bytes() == second.read_bytes()


def test_different_seeds_produce_different_matches() -> None:
    assert generate_match(1) != generate_match(2)


def test_match_round_trips_through_jsonl(tmp_path: Path) -> None:
    events = generate_match(1)
    path = tmp_path / "match.jsonl"
    write_match(events, path)
    assert read_match(path) == events


@pytest.mark.parametrize("seed", SEEDS)
def test_events_are_in_match_order(seed: int) -> None:
    events = generate_match(seed)
    stamps = [(e.minute, e.second) for e in events]
    assert stamps == sorted(stamps)
    assert [e.ts for e in events] == sorted(e.ts for e in events)


@pytest.mark.parametrize("seed", SEEDS)
def test_ids_are_unique(seed: int) -> None:
    events = generate_match(seed)
    assert len({e.id for e in events}) == len(events)


@pytest.mark.parametrize("seed", SEEDS)
def test_coordinates_are_within_pitch(seed: int) -> None:
    for event in generate_match(seed):
        for value in (event.x, event.end_x):
            if value is not None:
                assert 0 <= value <= 120
        for value in (event.y, event.end_y):
            if value is not None:
                assert 0 <= value <= 80


@pytest.mark.parametrize("seed", SEEDS)
def test_related_events_point_to_earlier_events(seed: int) -> None:
    events = generate_match(seed)
    position = {e.id: i for i, e in enumerate(events)}
    for index, event in enumerate(events):
        if event.related_event_id is not None:
            assert event.related_event_id in position
            assert position[event.related_event_id] < index


@pytest.mark.parametrize("seed", SEEDS)
def test_goals_and_saves_link_back_to_their_shot(seed: int) -> None:
    events = generate_match(seed)
    by_id = {e.id: e for e in events}
    for event in events:
        if event.type in (EventType.GOAL, EventType.SAVE):
            shot = by_id[event.related_event_id]
            assert shot.type is EventType.SHOT
            assert shot.outcome is (Outcome.GOAL if event.type is EventType.GOAL else Outcome.SAVED)


@pytest.mark.parametrize("seed", SEEDS)
def test_match_runs_about_ninety_minutes(seed: int) -> None:
    last = generate_match(seed)[-1]
    assert 90 <= last.minute <= 100


@pytest.mark.parametrize("seed", SEEDS)
def test_match_has_realistic_shape(seed: int) -> None:
    events = generate_match(seed)
    assert 1000 <= len(events) <= 4000
    for team in ("home", "away"):
        team_events = [e for e in events if e.team == team]
        passes = [e for e in team_events if e.type is EventType.PASS]
        assert len(passes) > 100
        assert any(e.type is EventType.SHOT for e in team_events)


def test_events_are_valid_models() -> None:
    assert all(isinstance(e, Event) for e in generate_match(1))


def test_generate_command_writes_match_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    output = tmp_path / "out" / "match.jsonl"
    assert main(["generate", "--seed", "1", "--output", str(output)]) == 0
    assert read_match(output) == generate_match(1)
    assert "wrote" in capsys.readouterr().out


def test_generate_command_defaults_to_data_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MID_DATA_DIR", str(tmp_path))
    assert main(["generate", "--seed", "4"]) == 0
    assert read_match(tmp_path / "match-4.jsonl") == generate_match(4)
