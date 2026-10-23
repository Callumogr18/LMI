from collections import deque
from dataclasses import dataclass, field

from mid.models import CardColor, Event, EventType, Fact, FactKind, FactScope
from mid.stats.calculations import calc_all, possession_pct


@dataclass
class MatchState:
    """
    Mutable state tracking the live match.
    
    Updated by the replayer as events stream in, consumed by agents.
    """
    
    match_id: str
    current_minute: int = 0
    current_second: int = 0
    
    # Score
    home_score: int = 0
    away_score: int = 0
    
    # Possession tracking
    home_possession_pct: float = 50.0
    away_possession_pct: float = 50.0
    total_passes: int = 0
    home_passes: int = 0
    away_passes: int = 0
    
    # Event counts by type
    home_shots: int = 0
    away_shots: int = 0
    home_goals: int = 0
    away_goals: int = 0
    home_dribbles: int = 0
    away_dribbles: int = 0
    home_tackles: int = 0
    away_tackles: int = 0
    home_interceptions: int = 0
    away_interceptions: int = 0
    home_clearances: int = 0
    away_clearances: int = 0
    home_fouls: int = 0
    away_fouls: int = 0
    home_yellow_cards: int = 0
    away_yellow_cards: int = 0
    home_red_cards: int = 0
    away_red_cards: int = 0
    home_saves: int = 0
    away_saves: int = 0
    
    # Last events for context
    last_event: Event | None = None
    last_goal_event: Event | None = None
    
    # Full event history and the latest Fact per (kind, scope)
    events: list[Event] = field(default_factory=list)
    facts: dict[str, Fact] = field(default_factory=dict)

    # Append-only history of every distinct Fact computed, in the order produced
    fact_log: list[Fact] = field(default_factory=list)
    facts_by_id: dict[str, Fact] = field(default_factory=dict)
    
    # Recent events for context (last 20 events)
    recent_events: deque[Event] = field(default_factory=lambda: deque(maxlen=20))
    recent_home_events: deque[Event] = field(default_factory=lambda: deque(maxlen=10))
    recent_away_events: deque[Event] = field(default_factory=lambda: deque(maxlen=10))
    
    def update(self, event: Event) -> list[Fact]:
        # Update state based on a new event; returns the Facts that changed as a result
        new_minute = event.minute != self.current_minute
        self.current_minute = event.minute
        self.current_second = event.second
        self.last_event = event
        self.events.append(event)
        
        # Add to recent events
        self.recent_events.append(event)
        if event.team == "home":
            self.recent_home_events.append(event)
        else:
            self.recent_away_events.append(event)
        
        if event.type == EventType.PASS:
            self.total_passes += 1
            if event.team == "home":
                self.home_passes += 1
            else:
                self.away_passes += 1
            self.home_possession_pct, self.away_possession_pct = possession_pct(self.home_passes, self.away_passes)
        
        elif event.type == EventType.SHOT:
            if event.team == "home":
                self.home_shots += 1
            else:
                self.away_shots += 1
        
        elif event.type == EventType.GOAL:
            self.last_goal_event = event
            if event.team == "home":
                self.home_score += 1
                self.home_goals += 1
            else:
                self.away_score += 1
                self.away_goals += 1
        
        elif event.type == EventType.CARRY or event.type == EventType.DRIBBLE:
            if event.team == "home":
                self.home_dribbles += 1
            else:
                self.away_dribbles += 1
        
        elif event.type == EventType.TACKLE:
            if event.team == "home":
                self.home_tackles += 1
            else:
                self.away_tackles += 1
        
        elif event.type == EventType.INTERCEPTION:
            if event.team == "home":
                self.home_interceptions += 1
            else:
                self.away_interceptions += 1
        
        elif event.type == EventType.CLEARANCE:
            if event.team == "home":
                self.home_clearances += 1
            else:
                self.away_clearances += 1
        
        elif event.type == EventType.FOUL:
            if event.team == "home":
                self.home_fouls += 1
            else:
                self.away_fouls += 1
        
        elif event.type == EventType.CARD:
            if event.card_color == CardColor.RED:
                if event.team == "home":
                    self.home_red_cards += 1
                else:
                    self.away_red_cards += 1
            else:
                if event.team == "home":
                    self.home_yellow_cards += 1
                else:
                    self.away_yellow_cards += 1

        elif event.type == EventType.SAVE:
            if event.team == "home":
                self.home_saves += 1
            else:
                self.away_saves += 1
        
        return self._refresh_facts(event.type, new_minute)
    
    def _refresh_facts(self, event_type: EventType, new_minute: bool) -> list[Fact]:
        # Recompute only the calculators the event affects; log a Fact only when it changed
        changed = []
        for fact in calc_all(self.events, event_type, new_minute):
            key = self._fact_key(fact.kind, fact.scope)
            latest = self.facts.get(key)
            if latest and (latest.value, latest.source_event_ids) == (
                fact.value,
                fact.source_event_ids,
            ):
                continue
            self.facts[key] = fact
            self.fact_log.append(fact)
            self.facts_by_id[fact.id] = fact
            changed.append(fact)
        return changed
    
    @staticmethod
    def _fact_key(kind: FactKind, scope: FactScope) -> str:
        return f"{kind}:{scope}"
    
    def get_fact(self, kind: FactKind, scope: FactScope = FactScope.MATCH) -> Fact | None:
        # Latest Fact for a stat; default scope is match-level stats such as tempo
        return self.facts.get(self._fact_key(kind, scope))
    
    def get_score(self):
        # Return formatted score string
        return f"{self.home_score}-{self.away_score}"
    
    def is_goal(self):
        # Check if the last event was a goal
        return self.last_event and self.last_event.type == EventType.GOAL
    
    def get_team_event_count(self, team: str, event_type: EventType):
        # Get event count for a specific team and event type
        if team == "home":
            mapping = {
                EventType.PASS: self.home_passes,
                EventType.SHOT: self.home_shots,
                EventType.GOAL: self.home_goals,
                EventType.CARRY: self.home_dribbles,
                EventType.DRIBBLE: self.home_dribbles,
                EventType.TACKLE: self.home_tackles,
                EventType.INTERCEPTION: self.home_interceptions,
                EventType.CLEARANCE: self.home_clearances,
                EventType.FOUL: self.home_fouls,
                EventType.CARD: self.home_yellow_cards + self.home_red_cards,
                EventType.SAVE: self.home_saves,
            }
        else:
            mapping = {
                EventType.PASS: self.away_passes,
                EventType.SHOT: self.away_shots,
                EventType.GOAL: self.away_goals,
                EventType.CARRY: self.away_dribbles,
                EventType.DRIBBLE: self.away_dribbles,
                EventType.TACKLE: self.away_tackles,
                EventType.INTERCEPTION: self.away_interceptions,
                EventType.CLEARANCE: self.away_clearances,
                EventType.FOUL: self.away_fouls,
                EventType.CARD: self.away_yellow_cards + self.away_red_cards,
                EventType.SAVE: self.away_saves,
            }
        return mapping.get(event_type, 0)
