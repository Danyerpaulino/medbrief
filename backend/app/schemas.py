from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _string_or_empty(value) -> str:
    if value is None:
        return ""
    return str(value)


def _string_or_na(value) -> str:
    if value is None or value == "":
        return "N/A"
    return str(value)


def _string_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item is not None]
    return [str(value)]


class Section(BaseModel):
    title: str = ""
    content: str = ""
    references: list[str] = Field(default_factory=list)

    @field_validator("title", "content", mode="before")
    @classmethod
    def coerce_text(cls, value) -> str:
        return _string_or_empty(value)

    @field_validator("references", mode="before")
    @classmethod
    def coerce_references(cls, value) -> list[str]:
        return _string_list(value)


class Treatment(BaseModel):
    name: str = ""
    phase: str = ""
    company: str = ""
    mechanism: str = ""
    description: str = ""
    trial_id: str | None = None

    @field_validator("name", "phase", "company", "mechanism", "description", mode="before")
    @classmethod
    def coerce_text(cls, value) -> str:
        return _string_or_empty(value)

    @field_validator("trial_id", mode="before")
    @classmethod
    def coerce_trial_id(cls, value) -> str | None:
        if value is None or value == "":
            return None
        return str(value)


class Player(BaseModel):
    name: str = ""
    type: str = ""
    role: str = ""

    @field_validator("name", "type", "role", mode="before")
    @classmethod
    def coerce_text(cls, value) -> str:
        return _string_or_empty(value)


class GroundingEntry(BaseModel):
    section: str = ""
    claim: str = ""
    supported: bool = False
    source_ids: list[str] = Field(default_factory=list)

    @field_validator("section", "claim", mode="before")
    @classmethod
    def coerce_text(cls, value) -> str:
        return _string_or_empty(value)

    @field_validator("source_ids", mode="before")
    @classmethod
    def coerce_source_ids(cls, value) -> list[str]:
        return _string_list(value)


class ConfidenceEntry(BaseModel):
    section: str = ""
    level: str = "limited"  # "strong", "moderate", "limited"
    source_count: int = 0
    newest_year: str = "N/A"
    oldest_year: str = "N/A"
    rationale: str = ""

    @field_validator("section", "rationale", mode="before")
    @classmethod
    def coerce_text(cls, value) -> str:
        return _string_or_empty(value)

    @field_validator("level", mode="before")
    @classmethod
    def normalize_level(cls, value) -> str:
        level = _string_or_empty(value).lower()
        if level not in {"strong", "moderate", "limited"}:
            return "limited"
        return level

    @field_validator("source_count", mode="before")
    @classmethod
    def coerce_source_count(cls, value) -> int:
        if value is None or value == "":
            return 0
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    @field_validator("newest_year", "oldest_year", mode="before")
    @classmethod
    def coerce_year(cls, value) -> str:
        return _string_or_na(value)


class BriefingResult(BaseModel):
    standard_of_care: list[Section] = Field(default_factory=list)
    emerging_treatments: list[Treatment] = Field(default_factory=list)
    key_players: list[Player] = Field(default_factory=list)
    summary: str = ""
    grounding: list[GroundingEntry] = Field(default_factory=list)
    confidence_scores: list[ConfidenceEntry] = Field(default_factory=list)

    @field_validator("summary", mode="before")
    @classmethod
    def coerce_summary(cls, value) -> str:
        return _string_or_empty(value)


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

    model_config = ConfigDict(from_attributes=True)
