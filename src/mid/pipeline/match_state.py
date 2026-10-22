from collections import deque
from dataclasses import dataclass, field

from mid.models import Event, EventType


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
    
    # Recent events for context (last 20 events)
    recent_events: deque[Event] = field(default_factory=lambda: deque(maxlen=20))
    recent_home_events: deque[Event] = field(default_factory=lambda: deque(maxlen=10))
    recent_away_events: deque[Event] = field(default_factory=lambda: deque(maxlen=10))
    
    def update(self, event: Event):
        # Update state based on a new event
        self.current_minute = event.minute
        self.current_second = event.second
        self.last_event = event
        
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
            self._update_possession()
        
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
            if event.team == "home":
                self.home_yellow_cards += 1
            else:
                self.away_yellow_cards += 1
        
        elif event.type == EventType.SAVE:
            if event.team == "home":
                self.home_saves += 1
            else:
                self.away_saves += 1
    
    def _update_possession(self):
        # Update possession percentage based on pass counts
        if self.total_passes > 0:
            self.home_possession_pct = (self.home_passes / self.total_passes) * 100
    
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
                EventType.CARD: self.home_yellow_cards,
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
                EventType.CARD: self.away_yellow_cards,
                EventType.SAVE: self.away_saves,
            }
        return mapping.get(event_type, 0)
