import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Briefing
from app.schemas import BriefingResult

logger = logging.getLogger(__name__)


def get_graph():
    from app.agent.graph import graph

    return graph


def normalize_agent_result(result: dict) -> dict:
    payload = {
        "standard_of_care": result.get("standard_of_care", []),
        "emerging_treatments": result.get("emerging_treatments", []),
        "key_players": result.get("key_players", []),
        "summary": result.get("summary", ""),
        "grounding": result.get("grounding", []),
        "confidence_scores": result.get("confidence_scores", []),
    }
    return BriefingResult.model_validate(payload).model_dump(mode="json")


async def run_briefing_agent(briefing_id: UUID):
    db: Session = SessionLocal()
    try:
        briefing = db.query(Briefing).filter(Briefing.id == briefing_id).first()
        if not briefing:
            logger.error(f"Briefing {briefing_id} not found")
            return

        briefing.status = "processing"
        db.commit()

        result = await get_graph().ainvoke({"condition": briefing.condition})

        briefing.result = normalize_agent_result(result)
        briefing.status = "completed"
        briefing.completed_at = datetime.now(timezone.utc)
        db.commit()

    except Exception as e:
        logger.exception(f"Briefing {briefing_id} failed")
        briefing = db.query(Briefing).filter(Briefing.id == briefing_id).first()
        if briefing:
            briefing.status = "failed"
            briefing.error = str(e)
            db.commit()
    finally:
        db.close()
