"""Fact: a deterministic, computed statement about the match, traceable to its events."""

from pydantic import BaseModel, ConfigDict, Field


class Fact(BaseModel):
    """A value computed by the stats stage. Narration may only cite Facts by id."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    value: float
    unit: str | None = None
    entity_refs: list[str] = Field(default_factory=list)
    source_event_ids: list[str] = Field(min_length=1)
    minute: int = Field(ge=0)
