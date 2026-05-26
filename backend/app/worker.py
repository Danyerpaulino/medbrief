import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.agent.graph import graph
from app.database import SessionLocal
from app.models import Briefing

logger = logging.getLogger(__name__)


async def run_briefing_agent(briefing_id: UUID):
    db: Session = SessionLocal()
    try:
        briefing = db.query(Briefing).filter(Briefing.id == briefing_id).first()
        if not briefing:
            logger.error(f"Briefing {briefing_id} not found")
            return

        briefing.status = "processing"
        db.commit()

        result = await graph.ainvoke({"condition": briefing.condition})

        briefing.result = {
            "standard_of_care": result["standard_of_care"],
            "emerging_treatments": result["emerging_treatments"],
            "key_players": result["key_players"],
            "summary": result["summary"],
        }
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
