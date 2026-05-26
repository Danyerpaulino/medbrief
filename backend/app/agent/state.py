from typing import TypedDict


class AgentState(TypedDict):
    condition: str
    pubmed_results: list[dict]
    clinical_trials: list[dict]
    standard_of_care: list[dict]
    emerging_treatments: list[dict]
    key_players: list[dict]
    summary: str
