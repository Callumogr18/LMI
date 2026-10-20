"""NarrativeItem: one line of commentary, with the Facts it cites and its verification status."""

from pydantic import BaseModel, ConfigDict, Field

from mid.models.enums import Audience, Status


class NarrativeItem(BaseModel):
    """A line of commentary. Status moves draft -> approved | rejected | fallback via the Critic."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    lang: str = Field(min_length=2, max_length=5)
    audience: Audience
    fact_ids: list[str] = Field(min_length=1)
    moment_type: str = Field(min_length=1)
    priority: int = Field(ge=0)
    status: Status = Status.DRAFT
    degraded: bool = False
