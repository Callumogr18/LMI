import math

from mid.models import Event, EventType, Fact, FactKind, FactScope, Outcome
from mid.models.pitch import PITCH_LENGTH, attack_direction

TEAMS = ("home", "away")
HALF_MINUTE = 45
LONG_PASS = 40.0
FINAL_THIRD_X = PITCH_LENGTH * 2 / 3
DEFENSIVE_ACTIONS = (EventType.TACKLE, EventType.INTERCEPTION, EventType.CLEARANCE, EventType.FOUL)

def _fact(
    kind: FactKind, team: str, value: float, unit: str, sources: list[Event], as_of: Event | None = None
) -> Fact:
    if team not in TEAMS:
        raise ValueError(f"team must be one of {TEAMS}, got {team!r}")
    return _build_fact(kind, FactScope(team), [team], value, unit, sources, as_of)


"""
Match-level facts for tempo stat
"""
def _match_fact(
    kind: FactKind, value: float, unit: str, sources: list[Event], as_of: Event | None = None
) -> Fact:
    return _build_fact(kind, FactScope.MATCH, [], value, unit, sources, as_of)


def _build_fact(
    kind: FactKind,
    scope: FactScope,
    refs: list[str],
    value: float,
    unit: str,
    sources: list[Event],
    as_of: Event | None = None,
) -> Fact:
    # The id is tied to the last event seen when the Fact was computed, so it is stable per state
    minute = max(e.minute for e in sources)
    return Fact(
        id=f"{kind}-{scope}-{(as_of or sources[-1]).id}",
        kind=kind,
        scope=scope,
        value=value,
        unit=unit,
        entity_refs=refs,
        source_event_ids=[e.id for e in sources],
        minute=minute,
    )


def _has_path(event: Event) -> bool:
    return None not in (event.x, event.y, event.end_x, event.end_y)


def _pass_length(event: Event) -> float:
    # Calculate Euclidean distance between start and end positions
    return math.hypot(event.end_x - event.x, event.end_y - event.y)


def _period(event: Event) -> int:
    # Events without an explicit period (older data) fall back to the 45th-minute boundary
    return event.period or (2 if event.minute >= HALF_MINUTE else 1)


def _attacking_x(x: float, event: Event) -> float:
    # x measured from the team's own goal line, so larger always means closer to the opponent goal.
    return x if attack_direction(event.team, _period(event)) > 0 else PITCH_LENGTH - x


def possession_pct(home_passes: int, away_passes: int) -> tuple[float, float]:
    # Pass share possession, 50/50 before any pass has been played
    total = home_passes + away_passes
    if not total:
        return 50.0, 50.0
    return home_passes / total * 100, away_passes / total * 100


def calc_possession_share(events: list[Event]) -> list[Fact]:
    # Possession share per team, as (team passes / total passes) * 100
    passes = [e for e in events if e.type == EventType.PASS]
    if not passes:
        return []
    home = [e for e in passes if e.team == "home"]
    shares = dict(zip(TEAMS, possession_pct(len(home), len(passes) - len(home))))
    return [_fact(FactKind.POSSESSION_SHARE, t, shares[t], "%", passes, events[-1]) for t in TEAMS]


def calc_pass_completion(events: list[Event]) -> list[Fact]:
    # Pass completion per team, as (successful passes / total passes) * 100
    facts = []
    for team in TEAMS:
        passes = [e for e in events if e.type == EventType.PASS and e.team == team]
        if passes:
            done = sum(e.outcome == Outcome.SUCCESS for e in passes)
            facts.append(_fact(FactKind.PASS_COMPLETION, team, done / len(passes) * 100, "%", passes, events[-1]))
    return facts


def calc_pass_distance(events: list[Event]) -> list[Fact]:
    # Mean pass length per team in pitch units, over passes with full coordinates
    facts = []
    for team in TEAMS:
        passes = [e for e in events if e.type == EventType.PASS and e.team == team and _has_path(e)]
        if passes:
            mean = sum(_pass_length(e) for e in passes) / len(passes)
            facts.append(_fact(FactKind.PASS_DISTANCE, team, mean, "m", passes, events[-1]))
    return facts


def _pass_difficulty(event: Event) -> float:
    # 0-1 score: 50% length, 30% forward progress, 20% ending in the final third
    length = min(_pass_length(event) / LONG_PASS, 1.0)
    start = _attacking_x(event.x, event)
    end = _attacking_x(event.end_x, event)
    forward = min(max(end - start, 0.0) / LONG_PASS, 1.0)
    return 0.5 * length + 0.3 * forward + 0.2 * (end >= FINAL_THIRD_X)


def calc_pass_difficulty(events: list[Event]) -> list[Fact]:
    # Mean heuristic pass difficulty (0-1) per team
    facts = []
    for team in TEAMS:
        passes = [e for e in events if e.type == EventType.PASS and e.team == team and _has_path(e)]
        if passes:
            mean = sum(_pass_difficulty(e) for e in passes) / len(passes)
            facts.append(_fact(FactKind.PASS_DIFFICULTY, team, mean, "score", passes, events[-1]))
    return facts


def calc_pressure(events: list[Event]) -> list[Fact]:
    # Defensive actions in the opponent's half per minute, per team (a high-press proxy).
    if not events:
        return []
    last = events[-1]
    elapsed = max(last.minute + last.second / 60, 1.0)
    facts = []
    for team in TEAMS:
        actions = [
            e for e in events
            if e.type in DEFENSIVE_ACTIONS
            and e.team == team
            and e.x is not None
            and _attacking_x(e.x, e) > PITCH_LENGTH / 2
        ]
        if actions:
            facts.append(_fact(FactKind.PRESSURE, team, len(actions) / elapsed, "actions/min", actions, last))
    return facts


def calc_tempo(events: list[Event], window_minutes: int | None = None) -> list[Fact]:
    # Events per minute across the match, optionally limited to the last `window_minutes`.
    if not events:
        return []
    last = events[-1]
    if window_minutes is not None:
        events = [e for e in events if e.minute > last.minute - window_minutes]
    elapsed = window_minutes or max(last.minute + last.second / 60, 1.0)
    return [_match_fact(FactKind.TEMPO, len(events) / elapsed, "events/min", events, last)]


def calc_shot_conversion(events: list[Event]) -> list[Fact]:
    # Shot conversion per team, as (goals / shots) * 100.
    facts = []
    for team in TEAMS:
        shots = [e for e in events if e.type == EventType.SHOT and e.team == team]
        if shots:
            goals = sum(e.outcome == Outcome.GOAL for e in shots)
            facts.append(_fact(FactKind.SHOT_CONVERSION, team, goals / len(shots) * 100, "%", shots, events[-1]))
    return facts


# (calculator, event types that change its result or None for any, whether elapsed time matters)
CALCULATORS = (
    (calc_possession_share, {EventType.PASS}, False),
    (calc_pass_completion, {EventType.PASS}, False),
    (calc_pass_distance, {EventType.PASS}, False),
    (calc_pass_difficulty, {EventType.PASS}, False),
    (calc_pressure, set(DEFENSIVE_ACTIONS), True),
    (calc_tempo, None, True),
    (calc_shot_conversion, {EventType.SHOT}, False),
)


def calc_all(
    events: list[Event], event_type: EventType | None = None, new_minute: bool = True
) -> list[Fact]:
    # Run the calculators affected by the latest event; with no event_type, run every calculator.
    # Time-dependent calculators (rates per minute) also refresh when the match minute advances.
    return [
        fact
        for calculator, triggers, time_dependent in CALCULATORS
        if event_type is None
        or triggers is None
        or event_type in triggers
        or (time_dependent and new_minute)
        for fact in calculator(events)
    ]
