from datetime import datetime, timezone
from uuid import uuid4

from app.schemas import BriefingResponse


def test_briefing_response_validates_nested_result():
    response = BriefingResponse.model_validate(
        {
            "id": uuid4(),
            "condition": "Non-Small Cell Lung Cancer",
            "status": "completed",
            "result": {
                "standard_of_care": [
                    {
                        "title": "First-line therapy",
                        "content": "Treatment depends on stage and biomarkers.",
                        "references": ["Smith et al., Oncology, 2025 (PMID: 12345)"],
                    }
                ],
                "emerging_treatments": [
                    {
                        "name": "Targeted therapy",
                        "phase": "Phase 3",
                        "company": "Acme Bio",
                        "mechanism": "Selective pathway inhibition",
                        "description": "Investigational treatment.",
                        "trial_id": "NCT00000001",
                    }
                ],
                "key_players": [
                    {
                        "name": "Academic Cancer Center",
                        "type": "academic",
                        "role": "Runs biomarker-driven trials.",
                    }
                ],
                "summary": "The landscape is shifting toward targeted care.",
            },
            "created_at": datetime.now(timezone.utc),
            "completed_at": datetime.now(timezone.utc),
        }
    )

    assert response.result is not None
    assert response.result.standard_of_care[0].references[0].startswith("Smith")
    assert response.result.emerging_treatments[0].trial_id == "NCT00000001"


def test_briefing_response_normalizes_llm_confidence_output():
    response = BriefingResponse.model_validate(
        {
            "id": uuid4(),
            "condition": "Heart Failure",
            "status": "completed",
            "result": {
                "standard_of_care": [],
                "emerging_treatments": [],
                "key_players": [],
                "summary": "Summary",
                "grounding": [
                    {
                        "section": "Care",
                        "claim": "Claim",
                        "supported": True,
                        "source_ids": "PMID:123",
                    }
                ],
                "confidence_scores": [
                    {},
                    {
                        "section": "Care",
                        "level": "Strong",
                        "source_count": "10",
                        "newest_year": 2026,
                        "oldest_year": None,
                        "rationale": None,
                    },
                    {
                        "section": "Emerging Treatments",
                        "level": "unknown",
                        "source_count": None,
                        "newest_year": None,
                        "oldest_year": "",
                        "rationale": "Sparse sources.",
                    },
                ],
            },
            "created_at": datetime.now(timezone.utc),
            "completed_at": datetime.now(timezone.utc),
        }
    )

    assert response.result is not None
    assert response.result.grounding[0].source_ids == ["PMID:123"]
    assert response.result.confidence_scores[0].level == "limited"
    assert response.result.confidence_scores[0].source_count == 0
    assert response.result.confidence_scores[1].level == "strong"
    assert response.result.confidence_scores[1].source_count == 10
    assert response.result.confidence_scores[1].newest_year == "2026"
    assert response.result.confidence_scores[1].oldest_year == "N/A"
    assert response.result.confidence_scores[1].rationale == ""
    assert response.result.confidence_scores[2].level == "limited"
    assert response.result.confidence_scores[2].source_count == 0
    assert response.result.confidence_scores[2].newest_year == "N/A"
