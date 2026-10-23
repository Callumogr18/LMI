"""Event: one raw, timed action in a match, as delivered by the synthetic feed."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from mid.models.enums import CardColor, EventType, Outcome


class Event(BaseModel):
    """A single match event. Immutable once ingested."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    match_id: str = Field(min_length=1)
    minute: int = Field(ge=0)
    second: int = Field(ge=0, le=59)
    type: EventType
    team: str = Field(min_length=1)
    player: str | None = None
    x: float | None = None
    y: float | None = None
    end_x: float | None = None
    end_y: float | None = None
    outcome: Outcome | None = None
    period: int | None = Field(default=None, ge=1, le=2)
    card_color: CardColor | None = None
    related_event_id: str | None = None
    ts: datetime
