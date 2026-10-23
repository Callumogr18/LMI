"""Tests for MatchState."""

import pytest
from datetime import UTC, datetime
from mid.models import CardColor, Event, EventType, FactKind, FactScope, Outcome
from mid.pipeline import MatchState


def test_match_state_initialization():
    """MatchState initializes with default values."""
    state = MatchState(match_id="match-1")
    assert state.match_id == "match-1"
    assert state.home_score == 0
    assert state.away_score == 0
    assert state.home_possession_pct == 50.0
    assert len(state.recent_events) == 0


def test_match_state_updates_with_pass():
    """Pass events update possession tracking."""
    state = MatchState(match_id="match-1")
    
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
    
    state.update(event)
    assert state.total_passes == 1
    assert state.home_passes == 1
    assert state.home_possession_pct == 100.0
    assert len(state.recent_events) == 1
    assert len(state.recent_home_events) == 1


def test_match_state_updates_with_goal():
    """Goal events update score."""
    state = MatchState(match_id="match-1")
    
    event = Event(
        id="match-1-e00001",
        match_id="match-1",
        minute=45,
        second=0,
        type=EventType.GOAL,
        team="home",
        player="Home #01",
        x=0.0,
        y=40.0,
        ts=datetime(2026, 10, 20, 15, 45, tzinfo=UTC),
    )
    
    state.update(event)
    assert state.home_score == 1
    assert state.away_score == 0
    assert state.get_score() == "1-0"
    assert state.is_goal()


def test_match_state_tracks_shots():
    """Shot events update shot counts."""
    state = MatchState(match_id="match-1")
    
    event = Event(
        id="match-1-e00001",
        match_id="match-1",
        minute=30,
        second=0,
        type=EventType.SHOT,
        team="away",
        player="Away #01",
        x=100.0,
        y=40.0,
        end_x=120.0,
        end_y=40.0,
        outcome=Outcome.GOAL,
        ts=datetime(2026, 10, 20, 15, 30, tzinfo=UTC),
    )
    
    state.update(event)
    assert state.away_shots == 1
    assert state.home_shots == 0


def test_match_state_possession_calculation():
    """Possession percentage is calculated correctly."""
    state = MatchState(match_id="match-1")
    
    # Add 3 home passes
    for i in range(3):
        event = Event(
            id=f"match-1-e{i:05d}",
            match_id="match-1",
            minute=0,
            second=i,
            type=EventType.PASS,
            team="home",
            player="Home #01",
            x=60.0,
            y=40.0,
            end_x=70.0,
            end_y=40.0,
            outcome=Outcome.SUCCESS,
            ts=datetime(2026, 10, 20, 15, 0, i, tzinfo=UTC),
        )
        state.update(event)
    
    # Add 1 away pass
    event = Event(
        id="match-1-e00004",
        match_id="match-1",
        minute=0,
        second=4,
        type=EventType.PASS,
        team="away",
        player="Away #01",
        x=60.0,
        y=40.0,
        end_x=50.0,
        end_y=40.0,
        outcome=Outcome.SUCCESS,
        ts=datetime(2026, 10, 20, 15, 0, 4, tzinfo=UTC),
    )
    state.update(event)
    
    assert state.total_passes == 4
    assert state.home_passes == 3
    assert state.away_passes == 1
    assert state.home_possession_pct == 75.0


def test_match_state_tracks_dribbles():
    """Dribble/carry events update dribble counts."""
    state = MatchState(match_id="match-1")
    
    event = Event(
        id="match-1-e00001",
        match_id="match-1",
        minute=15,
        second=0,
        type=EventType.DRIBBLE,
        team="home",
        player="Home #01",
        x=60.0,
        y=40.0,
        end_x=65.0,
        end_y=40.0,
        ts=datetime(2026, 10, 20, 15, 15, tzinfo=UTC),
    )
    
    state.update(event)
    assert state.home_dribbles == 1
    assert state.away_dribbles == 0


def test_match_state_tracks_defensive_actions():
    """Tackles, interceptions, and clearances are tracked."""
    state = MatchState(match_id="match-1")
    
    tackle = Event(
        id="match-1-e00001",
        match_id="match-1",
        minute=20,
        second=0,
        type=EventType.TACKLE,
        team="away",
        player="Away #01",
        x=50.0,
        y=40.0,
        outcome=Outcome.SUCCESS,
        ts=datetime(2026, 10, 20, 15, 20, tzinfo=UTC),
    )
    
    interception = Event(
        id="match-1-e00002",
        match_id="match-1",
        minute=21,
        second=0,
        type=EventType.INTERCEPTION,
        team="away",
        player="Away #02",
        x=55.0,
        y=40.0,
        outcome=Outcome.SUCCESS,
        ts=datetime(2026, 10, 20, 15, 21, tzinfo=UTC),
    )
    
    clearance = Event(
        id="match-1-e00003",
        match_id="match-1",
        minute=22,
        second=0,
        type=EventType.CLEARANCE,
        team="away",
        player="Away #03",
        x=10.0,
        y=40.0,
        end_x=40.0,
        end_y=40.0,
        ts=datetime(2026, 10, 20, 15, 22, tzinfo=UTC),
    )
    
    state.update(tackle)
    state.update(interception)
    state.update(clearance)
    
    assert state.away_tackles == 1
    assert state.away_interceptions == 1
    assert state.away_clearances == 1


def test_match_state_tracks_fouls_and_cards():
    """Fouls and cards are tracked."""
    state = MatchState(match_id="match-1")
    
    foul = Event(
        id="match-1-e00001",
        match_id="match-1",
        minute=25,
        second=0,
        type=EventType.FOUL,
        team="home",
        player="Home #01",
        x=50.0,
        y=40.0,
        ts=datetime(2026, 10, 20, 15, 25, tzinfo=UTC),
    )
    
    card = Event(
        id="match-1-e00002",
        match_id="match-1",
        minute=25,
        second=5,
        type=EventType.CARD,
        team="home",
        player="Home #01",
        x=50.0,
        y=40.0,
        ts=datetime(2026, 10, 20, 15, 25, 5, tzinfo=UTC),
    )
    
    state.update(foul)
    state.update(card)
    
    assert state.home_fouls == 1
    assert state.home_yellow_cards == 1


def test_match_state_tracks_saves():
    """Saves are tracked."""
    state = MatchState(match_id="match-1")
    
    save = Event(
        id="match-1-e00001",
        match_id="match-1",
        minute=30,
        second=0,
        type=EventType.SAVE,
        team="away",
        player="Away #01",
        x=0.0,
        y=40.0,
        ts=datetime(2026, 10, 20, 15, 30, tzinfo=UTC),
    )
    
    state.update(save)
    assert state.away_saves == 1


def test_match_state_recent_events():
    """Recent events are tracked with max length."""
    state = MatchState(match_id="match-1")
    
    # Add 25 events
    for i in range(25):
        event = Event(
            id=f"match-1-e{i:05d}",
            match_id="match-1",
            minute=0,
            second=i,
            type=EventType.PASS,
            team="home" if i % 2 == 0 else "away",
            player="Home #01" if i % 2 == 0 else "Away #01",
            x=60.0,
            y=40.0,
            end_x=70.0,
            end_y=40.0,
            outcome=Outcome.SUCCESS,
            ts=datetime(2026, 10, 20, 15, 0, i, tzinfo=UTC),
        )
        state.update(event)
    
    # Should only keep last 20
    assert len(state.recent_events) == 20
    # Should only keep last 10 per team
    assert len(state.recent_home_events) == 10
    assert len(state.recent_away_events) == 10


def test_match_state_get_team_event_count():
    """get_team_event_count returns correct counts."""
    state = MatchState(match_id="match-1")
    
    # Add various events
    for i in range(5):
        event = Event(
            id=f"match-1-e{i:05d}",
            match_id="match-1",
            minute=0,
            second=i,
            type=EventType.PASS,
            team="home",
            player="Home #01",
            x=60.0,
            y=40.0,
            end_x=70.0,
            end_y=40.0,
            outcome=Outcome.SUCCESS,
            ts=datetime(2026, 10, 20, 15, 0, i, tzinfo=UTC),
        )
        state.update(event)
    
    assert state.get_team_event_count("home", EventType.PASS) == 5
    assert state.get_team_event_count("away", EventType.PASS) == 0


def test_match_state_accumulates_facts_with_source_events():
    """Facts are recomputed as events arrive and trace back to event IDs."""
    state = MatchState(match_id="match-1")
    assert state.get_fact(FactKind.POSSESSION_SHARE, FactScope.HOME) is None

    ids = []
    for i, team in enumerate(["home", "home", "away"]):
        event = Event(
            id=f"match-1-e{i:05d}",
            match_id="match-1",
            minute=i,
            second=0,
            type=EventType.PASS,
            team=team,
            player=f"{team} #01",
            x=60.0,
            y=40.0,
            end_x=70.0,
            end_y=40.0,
            outcome=Outcome.SUCCESS,
            ts=datetime(2026, 10, 20, 15, i, tzinfo=UTC),
        )
        ids.append(event.id)
        state.update(event)

    home = state.get_fact(FactKind.POSSESSION_SHARE, FactScope.HOME)
    assert home.value == pytest.approx(200 / 3)
    assert home.source_event_ids == ids
    assert home.minute == 2
    assert state.get_fact(FactKind.PASS_COMPLETION, FactScope.AWAY).value == 100.0
    assert state.get_fact(FactKind.TEMPO).entity_refs == []
    assert len(state.facts) == len({f.id for f in state.facts.values()})


def test_match_state_counts_red_and_yellow_cards():
    state = MatchState(match_id="match-1")
    for i, color in enumerate([CardColor.RED, CardColor.YELLOW, None]):
        state.update(Event(
            id=f"match-1-e{i:05d}", match_id="match-1", minute=1, second=i,
            type=EventType.CARD, team="away", player="Away #02", card_color=color,
            ts=datetime(2026, 10, 20, 15, 1, i, tzinfo=UTC),
        ))
    assert (state.away_red_cards, state.away_yellow_cards) == (1, 2)
    assert state.get_team_event_count("away", EventType.CARD) == 3


def test_fact_ids_are_stable_and_log_is_append_only():
    state = MatchState(match_id="match-1")
    seen = {}
    for i, team in enumerate(["home", "away", "home"]):
        state.update(Event(
            id=f"match-1-e{i:05d}", match_id="match-1", minute=5, second=i,
            type=EventType.PASS, team=team, player="p", x=60.0, y=40.0, end_x=70.0, end_y=40.0,
            outcome=Outcome.SUCCESS, ts=datetime(2026, 10, 20, 15, 5, i, tzinfo=UTC),
        ))
        seen[state.get_fact(FactKind.POSSESSION_SHARE, FactScope.HOME).id] = state.get_fact(FactKind.POSSESSION_SHARE, FactScope.HOME).value
    assert len(seen) == 3
    ids = [f.id for f in state.fact_log]
    assert len(ids) == len(set(ids))
    for fact_id, value in seen.items():
        assert state.facts_by_id[fact_id].value == value
