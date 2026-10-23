from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from mid.models import Audience, Event, EventType, Fact, FactKind, FactScope, NarrativeItem, Outcome, Status

TS = datetime(2026, 10, 20, 15, 0, tzinfo=UTC)


def make_event(**overrides) -> Event:
    fields = {
        "id": "e1",
        "match_id": "m1",
        "minute": 12,
        "second": 30,
        "type": EventType.PASS,
        "team": "home",
        "player": "Player 7",
        "x": 60.0,
        "y": 40.0,
        "end_x": 80.5,
        "end_y": 35.0,
        "outcome": Outcome.SUCCESS,
        "related_event_id": None,
        "ts": TS,
    }
    fields.update(overrides)
    return Event(**fields)


def make_fact(**overrides) -> Fact:
    fields = {
        "id": "f1",
        "kind": FactKind.PASS_DISTANCE,
        "scope": FactScope.HOME,
        "value": 21.4,
        "unit": "m",
        "entity_refs": ["Player 7"],
        "source_event_ids": ["e1"],
        "minute": 12,
    }
    fields.update(overrides)
    return Fact(**fields)


def make_narrative(**overrides) -> NarrativeItem:
    fields = {
        "id": "n1",
        "text": "Player 7 slides a 21.4 m pass into the box.",
        "lang": "en",
        "audience": Audience.ANALYST,
        "fact_ids": ["f1"],
        "moment_type": "progression",
        "priority": 2,
    }
    fields.update(overrides)
    return NarrativeItem(**fields)


def test_event_round_trips_through_json() -> None:
    event = make_event()
    assert Event.model_validate_json(event.model_dump_json()) == event


def test_event_optional_fields_can_be_missing() -> None:
    event = make_event(player=None, x=None, y=None, end_x=None, end_y=None, outcome=None)
    assert event.outcome is None and event.player is None


def test_event_is_immutable() -> None:
    with pytest.raises(ValidationError):
        make_event().minute = 13


@pytest.mark.parametrize(
    "overrides",
    [{"minute": -1}, {"second": 60}, {"id": ""}, {"type": "dive"}, {"outcome": "maybe"}],
)
def test_event_rejects_invalid_values(overrides: dict) -> None:
    with pytest.raises(ValidationError):
        make_event(**overrides)


def test_event_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        Event(**make_event().model_dump(), xg=0.1)


def test_fact_requires_source_events() -> None:
    with pytest.raises(ValidationError):
        make_fact(source_event_ids=[])


def test_fact_entity_refs_default_to_empty() -> None:
    fact = Fact(id="f2", kind=FactKind.POSSESSION_SHARE, scope=FactScope.MATCH, value=54.0, source_event_ids=["e1"], minute=5)
    assert fact.entity_refs == [] and fact.unit is None


def test_fact_round_trips_through_json() -> None:
    fact = make_fact()
    assert Fact.model_validate_json(fact.model_dump_json()) == fact


def test_narrative_defaults_to_draft_not_degraded() -> None:
    item = make_narrative()
    assert item.status is Status.DRAFT
    assert item.degraded is False


def test_narrative_requires_cited_facts() -> None:
    with pytest.raises(ValidationError):
        make_narrative(fact_ids=[])


def test_narrative_rejects_unknown_audience_and_status() -> None:
    with pytest.raises(ValidationError):
        make_narrative(audience="coach")
    with pytest.raises(ValidationError):
        make_narrative(status="published")


def test_narrative_accepts_all_statuses() -> None:
    for status in Status:
        assert make_narrative(status=status.value).status is status


def test_narrative_round_trips_through_json() -> None:
    item = make_narrative(status=Status.APPROVED, degraded=True)
    assert NarrativeItem.model_validate_json(item.model_dump_json()) == item


def test_enum_values_match_spec_vocabulary() -> None:
    assert {a.value for a in Audience} == {"analyst", "fan"}
    assert {s.value for s in Status} == {"draft", "approved", "rejected", "fallback"}
