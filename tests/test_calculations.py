"""Tests for match statistics calculations."""

from datetime import UTC, datetime, timedelta

import pytest

from mid.generator.synthetic import generate_match
from mid.models import Event, EventType, FactKind, Outcome
from mid.stats import calculations as calc

_counter = 0


def make_event(type=EventType.PASS, team="home", minute=0, second=0, x=60.0, y=40.0,
               end_x=70.0, end_y=40.0, outcome=Outcome.SUCCESS):
    global _counter
    _counter += 1
    return Event(
        id=f"match-1-e{_counter:05d}",
        match_id="match-1",
        minute=minute,
        second=second,
        type=type,
        team=team,
        player=f"{team} #01",
        x=x,
        y=y,
        end_x=end_x,
        end_y=end_y,
        outcome=outcome,
        ts=datetime(2026, 10, 20, 15, 0, tzinfo=UTC) + timedelta(minutes=minute, seconds=second),
    )


def by_team(facts):
    return {f.entity_refs[0]: f for f in facts}


def test_possession_pct_defaults_to_even_split():
    assert calc.possession_pct(0, 0) == (50.0, 50.0)


def test_possession_pct_split():
    assert calc.possession_pct(3, 1) == (75.0, 25.0)


def test_possession_share_per_team():
    events = [make_event(team="home") for _ in range(3)] + [make_event(team="away")]
    facts = by_team(calc.calc_possession_share(events))
    assert facts["home"].value == 75.0
    assert facts["away"].value == 25.0
    assert facts["home"].kind == FactKind.POSSESSION_SHARE
    assert len(facts["home"].source_event_ids) == 4


def test_possession_share_no_passes_returns_nothing():
    assert calc.calc_possession_share([make_event(type=EventType.SHOT)]) == []
    assert calc.calc_possession_share([]) == []


def test_pass_completion_is_per_team():
    events = [
        make_event(team="home"),
        make_event(team="home", outcome=Outcome.FAILURE),
        make_event(team="away"),
    ]
    facts = by_team(calc.calc_pass_completion(events))
    assert facts["home"].value == 50.0
    assert facts["away"].value == 100.0


def test_pass_completion_skips_team_without_passes():
    facts = calc.calc_pass_completion([make_event(team="home")])
    assert [f.entity_refs for f in facts] == [["home"]]


def test_pass_distance_mean_and_skips_missing_coordinates():
    events = [
        make_event(x=0.0, y=0.0, end_x=3.0, end_y=4.0),
        make_event(x=0.0, y=0.0, end_x=10.0, end_y=0.0),
        make_event(end_x=None, end_y=None),
    ]
    fact = by_team(calc.calc_pass_distance(events))["home"]
    assert fact.value == pytest.approx(7.5)
    assert len(fact.source_event_ids) == 2


def test_pass_difficulty_long_forward_final_third_scores_highest():
    hard = make_event(x=60.0, end_x=110.0)
    easy = make_event(x=60.0, end_x=61.0)
    assert by_team(calc.calc_pass_difficulty([hard]))["home"].value == pytest.approx(1.0)
    assert by_team(calc.calc_pass_difficulty([easy]))["home"].value < 0.1


def test_pass_difficulty_respects_attack_direction():
    away_forward = make_event(team="away", x=60.0, end_x=10.0)
    away_backward = make_event(team="away", x=60.0, end_x=110.0)
    forward = by_team(calc.calc_pass_difficulty([away_forward]))["away"].value
    backward = by_team(calc.calc_pass_difficulty([away_backward]))["away"].value
    assert forward > backward


def test_pass_difficulty_attack_direction_flips_after_half_time():
    first = make_event(team="home", minute=10, x=60.0, end_x=110.0)
    second = make_event(team="home", minute=60, x=60.0, end_x=110.0)
    assert (
        by_team(calc.calc_pass_difficulty([first]))["home"].value
        > by_team(calc.calc_pass_difficulty([second]))["home"].value
    )


def test_pressure_counts_only_opponent_half_defensive_actions():
    events = [
        make_event(type=EventType.TACKLE, team="home", x=90.0, minute=0),
        make_event(type=EventType.TACKLE, team="home", x=20.0, minute=1),
        make_event(type=EventType.PASS, team="home", x=90.0, minute=1),
        make_event(type=EventType.INTERCEPTION, team="home", x=100.0, minute=2),
    ]
    fact = by_team(calc.calc_pressure(events))["home"]
    assert fact.value == pytest.approx(2 / 2.0)
    assert len(fact.source_event_ids) == 2
    assert "away" not in by_team(calc.calc_pressure(events))


def test_pressure_away_uses_mirrored_half():
    events = [make_event(type=EventType.TACKLE, team="away", x=20.0, minute=1)]
    assert by_team(calc.calc_pressure(events))["away"].value == pytest.approx(1.0)


def test_tempo_is_a_single_match_level_fact():
    events = [make_event(team="home", minute=m) for m in range(0, 10)] + [make_event(team="away", minute=10)]
    facts = calc.calc_tempo(events)
    assert len(facts) == 1
    assert facts[0].entity_refs == []
    assert facts[0].id == f"tempo-match-{events[-1].id}"
    assert facts[0].value == pytest.approx(11 / 10)


def test_tempo_window_limits_events():
    events = [make_event(minute=m) for m in range(0, 20)]
    fact = calc.calc_tempo(events, window_minutes=5)[0]
    assert fact.value == pytest.approx(5 / 5)
    assert len(fact.source_event_ids) == 5


def test_tempo_empty():
    assert calc.calc_tempo([]) == []


def test_shot_conversion_per_team():
    events = [
        make_event(type=EventType.SHOT, outcome=Outcome.GOAL),
        make_event(type=EventType.SHOT, outcome=Outcome.SAVED),
        make_event(type=EventType.SHOT, team="away", outcome=Outcome.OFF_TARGET),
    ]
    facts = by_team(calc.calc_shot_conversion(events))
    assert facts["home"].value == 50.0
    assert facts["away"].value == 0.0


def test_fact_rejects_invalid_team():
    with pytest.raises(ValueError):
        calc._fact("x", "neither", 1.0, "u", [make_event()])


def test_all_calcs_produce_valid_facts_on_generated_match():
    events = generate_match(1)
    for fn in (
        calc.calc_possession_share,
        calc.calc_pass_completion,
        calc.calc_pass_distance,
        calc.calc_pass_difficulty,
        calc.calc_pressure,
        calc.calc_tempo,
        calc.calc_shot_conversion,
    ):
        facts = fn(events)
        assert facts
        assert all(f.source_event_ids for f in facts)


def test_generated_events_carry_period_and_late_first_half_uses_first_half_direction():
    events = generate_match(1)
    assert {e.period for e in events} == {1, 2}
    late_first = [e for e in events if e.period == 1 and e.minute >= 45 and e.type == EventType.PASS and e.team == "home" and _has(e)]
    assert late_first
    assert all(calc._attacking_x(e.x, e) == e.x for e in late_first)


def _has(e):
    return calc._has_path(e)


def test_fact_ids_differ_when_state_differs():
    a = make_event(team="home")
    b = make_event(team="home")
    assert calc.calc_possession_share([a])[0].id != calc.calc_possession_share([a, b])[0].id
