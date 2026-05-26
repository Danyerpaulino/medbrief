from typing import TypedDict


class ConfidenceScore(TypedDict):
    section: str
    level: str  # "strong", "moderate", "limited"
    source_count: int
    newest_year: str
    oldest_year: str
    rationale: str


class GroundingResult(TypedDict):
    section: str
    claim: str
    supported: bool
    source_ids: list[str]  # PMIDs or NCT IDs


class AgentState(TypedDict):
    condition: str
    pubmed_results: list[dict]
    clinical_trials: list[dict]
    standard_of_care: list[dict]
    emerging_treatments: list[dict]
    key_players: list[dict]
    summary: str
    confidence_scores: list[dict]
    grounding: list[dict]
