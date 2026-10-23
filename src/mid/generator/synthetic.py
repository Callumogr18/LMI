"""Seeded synthetic match generator.

Produces one football-realistic match as a time-ordered stream of Events. All randomness comes
from a single seeded RNG and timestamps are derived from a fixed kickoff, so the same seed always
yields the same events. No real match data is used.
"""

import math
import random
from datetime import UTC, datetime, timedelta

from mid.models import CardColor, Event, EventType, Outcome
from mid.models.pitch import PITCH_LENGTH, PITCH_WIDTH, attack_direction
BOX_DEPTH = 18.0
BOX_WIDTH_MARGIN = 18.0
HALF_SECONDS = 45 * 60
KICKOFF = datetime(2026, 10, 20, 15, 0, tzinfo=UTC)
TEAMS = ("home", "away")
TEAM_LABELS = {"home": "Home", "away": "Away"}
SQUAD_SIZE = 11
GOALKEEPER_NUMBER = 1

PASS_SUCCESS_BASE = 0.92
PASS_SUCCESS_MIN = 0.5
PASS_SUCCESS_MAX = 0.95
PASS_DISTANCE_PENALTY = 0.012
SHOT_CHANCE_IN_BOX = 0.3
CARRY_CHANCE = 0.25
FOUL_CHANCE_ON_TURNOVER = 0.07
CARD_CHANCE_ON_FOUL = 0.25
RED_CARD_SHARE = 0.1
GOAL_SHARE = 0.12
SAVED_SHARE = 0.35
BLOCKED_SHARE = 0.20


def generate_match(seed: int, match_id: str | None = None) -> list[Event]:
    """Return one synthetic match for `seed`, ordered by match clock."""
    return _MatchBuilder(random.Random(seed), match_id or f"match-{seed}").run()


class _MatchBuilder:
    def __init__(self, rng: random.Random, match_id: str) -> None:
        self._rng = rng
        self._match_id = match_id
        self._events: list[Event] = []
        self._clock = 0  # whole match seconds
        self._period = 1

    def run(self) -> list[Event]:
        rng = self._rng
        # Match clock skips the half-time break, as real match minutes do.
        first_half_end = HALF_SECONDS + rng.randint(60, 180)
        second_half_start = first_half_end
        match_end = second_half_start + HALF_SECONDS + rng.randint(120, 300)

        team = TEAMS[0]
        x, y = PITCH_LENGTH / 2, PITCH_WIDTH / 2
        second_half = False
        kickoff = True
        while self._clock < match_end:
            if not second_half and self._clock >= first_half_end:
                self._clock = second_half_start
                second_half = True
                self._period = 2

            if not kickoff:
                self._recover(team, x, y)
            kickoff = False

            direction = attack_direction(team, self._period)
            x, y, lost_ball = self._possession(team, direction, x, y)
            losing_team = team
            team = _other(team)

            if lost_ball and rng.random() < FOUL_CHANCE_ON_TURNOVER:
                self._foul(losing_team, x, y)
            self._clock += rng.randint(2, 8)
        return self._events

    def _possession(
        self, team: str, direction: int, x: float, y: float
    ) -> tuple[float, float, bool]:
        """Play one spell of possession. Returns the ball position and whether it was lost."""
        rng = self._rng
        last_pass_id: str | None = None
        goal_x = PITCH_LENGTH if direction > 0 else 0.0
        for _ in range(rng.randint(4, 15)):
            depth = abs(goal_x - x)
            in_box = depth <= BOX_DEPTH and BOX_WIDTH_MARGIN <= y <= PITCH_WIDTH - BOX_WIDTH_MARGIN
            if in_box and rng.random() < SHOT_CHANCE_IN_BOX:
                self._shot(team, x, y, goal_x, last_pass_id)
                return x, y, False

            end_x = _clamp_x(x + direction * rng.uniform(-4, 22))
            end_y = _clamp_y(y + rng.gauss(0, 10))
            distance = math.dist((x, y), (end_x, end_y))
            p_success = min(
                PASS_SUCCESS_MAX,
                max(PASS_SUCCESS_MIN, PASS_SUCCESS_BASE - PASS_DISTANCE_PENALTY * distance),
            )
            success = rng.random() < p_success
            passer = self._player(team)
            pass_event = self._add(
                EventType.PASS,
                team,
                passer,
                x,
                y,
                end_x=end_x,
                end_y=end_y,
                outcome=Outcome.SUCCESS if success else Outcome.FAILURE,
                related=last_pass_id,
            )
            self._clock += rng.randint(1, 4)
            last_pass_id = pass_event.id
            if not success:
                return end_x, end_y, True

            x, y = end_x, end_y
            if rng.random() < CARRY_CHANCE:
                carry_x = _clamp_x(x + direction * rng.uniform(2, 8))
                carry_y = _clamp_y(y + rng.gauss(0, 3))
                self._add(EventType.CARRY, team, passer, x, y, end_x=carry_x, end_y=carry_y)
                self._clock += rng.randint(1, 3)
                x, y = carry_x, carry_y
        return x, y, False

    def _shot(self, team: str, x: float, y: float, goal_x: float, assist_id: str | None) -> None:
        rng = self._rng
        shooter = self._player(team)
        roll = rng.random()
        if roll < GOAL_SHARE:
            outcome = Outcome.GOAL
        elif roll < GOAL_SHARE + SAVED_SHARE:
            outcome = Outcome.SAVED
        elif roll < GOAL_SHARE + SAVED_SHARE + BLOCKED_SHARE:
            outcome = Outcome.BLOCKED
        else:
            outcome = Outcome.OFF_TARGET

        shot = self._add(
            EventType.SHOT,
            team,
            shooter,
            x,
            y,
            end_x=goal_x,
            end_y=y,
            outcome=outcome,
            related=assist_id,
        )
        if outcome is Outcome.GOAL:
            self._add(EventType.GOAL, team, shooter, goal_x, y, related=shot.id)
        elif outcome is Outcome.SAVED:
            keeper = self._goalkeeper(_other(team))
            self._add(EventType.SAVE, _other(team), keeper, goal_x, y, related=shot.id)
        self._clock += rng.randint(2, 6)

    def _recover(self, team: str, x: float, y: float) -> None:
        kind = self._rng.choice((EventType.TACKLE, EventType.INTERCEPTION))
        self._add(kind, team, self._player(team), x, y, outcome=Outcome.SUCCESS)
        self._clock += self._rng.randint(1, 3)

    def _foul(self, team: str, x: float, y: float) -> None:
        rng = self._rng
        player = self._player(team)
        foul = self._add(EventType.FOUL, team, player, x, y)
        if rng.random() < CARD_CHANCE_ON_FOUL:
            color = CardColor.RED if rng.random() < RED_CARD_SHARE else CardColor.YELLOW
            self._add(EventType.CARD, team, player, x, y, related=foul.id, card_color=color)
        self._clock += rng.randint(3, 10)

    def _player(self, team: str) -> str:
        number = self._rng.randint(1, SQUAD_SIZE)
        return f"{TEAM_LABELS[team]} #{number:02d}"

    def _goalkeeper(self, team: str) -> str:
        return f"{TEAM_LABELS[team]} #{GOALKEEPER_NUMBER:02d}"

    def _add(
        self,
        event_type: EventType,
        team: str,
        player: str,
        x: float,
        y: float,
        *,
        end_x: float | None = None,
        end_y: float | None = None,
        outcome: Outcome | None = None,
        related: str | None = None,
        card_color: CardColor | None = None,
    ) -> Event:
        minute, second = divmod(self._clock, 60)
        event = Event(
            # Saves a match event with an id of seed and 
            # a 5 digit event number, avg around ~1700 events/pm
            id=f"{self._match_id}-e{len(self._events) + 1:05d}",
            match_id=self._match_id,
            minute=minute,
            second=second,
            type=event_type,
            team=team,
            player=player,
            x=_round(x),
            y=_round(y),
            end_x=_round(end_x),
            end_y=_round(end_y),
            outcome=outcome,
            related_event_id=related,
            period=self._period,
            card_color=card_color,
            # Save event with a timestamp of kickoff + clock seconds,
            # divmod returns min, secs from total seconds tracked so far
            ts=KICKOFF + timedelta(seconds=self._clock),
        )
        self._events.append(event)
        return event


def _other(team: str) -> str:
    return TEAMS[1] if team == TEAMS[0] else TEAMS[0]


def _clamp_x(value: float) -> float:
    return min(max(value, 0.5), PITCH_LENGTH - 0.5)


def _clamp_y(value: float) -> float:
    return min(max(value, 0.5), PITCH_WIDTH - 0.5)


def _round(value: float | None) -> float | None:
    return None if value is None else round(value, 1)
