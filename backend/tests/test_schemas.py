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
