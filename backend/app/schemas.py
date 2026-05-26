from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class Section(BaseModel):
    title: str
    content: str
    references: list[str]


class Treatment(BaseModel):
    name: str
    phase: str
    company: str
    mechanism: str
    description: str
    trial_id: str | None = None


class Player(BaseModel):
    name: str
    type: str
    role: str


class GroundingEntry(BaseModel):
    section: str
    claim: str
    supported: bool
    source_ids: list[str] = []


class ConfidenceEntry(BaseModel):
    section: str
    level: str  # "strong", "moderate", "limited"
    source_count: int
    newest_year: str = "N/A"
    oldest_year: str = "N/A"
    rationale: str


class BriefingResult(BaseModel):
    standard_of_care: list[Section]
    emerging_treatments: list[Treatment]
    key_players: list[Player]
    summary: str
    grounding: list[GroundingEntry] = []
    confidence_scores: list[ConfidenceEntry] = []


class BriefingCreate(BaseModel):
    condition: str


class BriefingResponse(BaseModel):
    id: UUID
    condition: str
    status: str
    result: BriefingResult | None = None
    error: str | None = None
    created_at: datetime
    completed_at: datetime | None = None

    class Config:
        from_attributes = True
