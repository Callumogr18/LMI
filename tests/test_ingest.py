"""Tests for event ingestion."""

from datetime import UTC, datetime
from mid.models import Event, EventType, Outcome
from mid.validator import ingest_events


def test_ingest_deduplicates():
    """Duplicate events by ID are removed."""
    event = Event(
        id="match-1-e00001",
        match_id="match-1",
        minute=0,
        second=0,
        type=EventType.PASS,
        team="home",
        player="Home #01",
        x=60.0,
        y=40.0,
        end_x=70.0,
        end_y=40.0,
        outcome=Outcome.SUCCESS,
        ts=datetime(2026, 10, 20, 15, 0, tzinfo=UTC),
    )
    result = ingest_events([event, event])
    assert len(result) == 1
    assert result[0].id == "match-1-e00001"


def test_ingest_orders_by_timestamp():
    """Events are sorted chronologically."""
    early = Event(
        id="match-1-e00001",
        match_id="match-1",
        minute=0,
        second=0,
        type=EventType.PASS,
        team="home",
        player="Home #01",
        x=60.0,
        y=40.0,
        end_x=70.0,
        end_y=40.0,
        outcome=Outcome.SUCCESS,
        ts=datetime(2026, 10, 20, 15, 0, tzinfo=UTC),
    )
    late = Event(
        id="match-1-e00002",
        match_id="match-1",
        minute=0,
        second=5,
        type=EventType.PASS,
        team="home",
        player="Home #02",
        x=70.0,
        y=40.0,
        end_x=80.0,
        end_y=40.0,
        outcome=Outcome.SUCCESS,
        ts=datetime(2026, 10, 20, 15, 0, 5, tzinfo=UTC),
    )
    result = ingest_events([late, early])
    assert result[0].id == "match-1-e00001"
    assert result[1].id == "match-1-e00002"


def test_ingest_filters_invalid_coordinates():
    """Events with out-of-bounds coordinates are rejected."""
    invalid = Event(
        id="match-1-e00001",
        match_id="match-1",
        minute=0,
        second=0,
        type=EventType.PASS,
        team="home",
        player="Home #01",
        x=200.0,  # Invalid: beyond pitch length
        y=40.0,
        end_x=70.0,
        end_y=40.0,
        outcome=Outcome.SUCCESS,
        ts=datetime(2026, 10, 20, 15, 0, tzinfo=UTC),
    )
    result = ingest_events([invalid])
    assert len(result) == 0


def test_ingest_filters_invalid_outcome():
    """Events with inconsistent type/outcome pairs are rejected."""
    invalid = Event(
        id="match-1-e00001",
        match_id="match-1",
        minute=0,
        second=0,
        type=EventType.SHOT,
        team="home",
        player="Home #01",
        x=100.0,
        y=40.0,
        end_x=120.0,
        end_y=40.0,
        outcome=Outcome.SUCCESS,  # Invalid: shots can't have SUCCESS outcome
        ts=datetime(2026, 10, 20, 15, 0, tzinfo=UTC),
    )
    result = ingest_events([invalid])
    assert len(result) == 0


def test_ingest_passes_valid_events():
    """Valid events pass through unchanged."""
    valid = Event(
        id="match-1-e00001",
        match_id="match-1",
        minute=0,
        second=0,
        type=EventType.PASS,
        team="home",
        player="Home #01",
        x=60.0,
        y=40.0,
        end_x=70.0,
        end_y=40.0,
        outcome=Outcome.SUCCESS,
        ts=datetime(2026, 10, 20, 15, 0, tzinfo=UTC),
    )
    result = ingest_events([valid])
    assert len(result) == 1
    assert result[0].id == "match-1-e00001"
