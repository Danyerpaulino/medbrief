import asyncio
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Briefing
from app.schemas import BriefingCreate, BriefingResponse
from app.worker import run_briefing_agent

router = APIRouter(prefix="/api/briefings", tags=["briefings"])


@router.post("", response_model=BriefingResponse, status_code=201)
def create_briefing(payload: BriefingCreate, db: Session = Depends(get_db)):
    briefing = Briefing(condition=payload.condition)
    db.add(briefing)
    db.commit()
    db.refresh(briefing)
    asyncio.create_task(run_briefing_agent(briefing.id))
    return briefing


@router.get("", response_model=list[BriefingResponse])
def list_briefings(db: Session = Depends(get_db)):
    return db.query(Briefing).order_by(Briefing.created_at.desc()).all()


@router.get("/{briefing_id}", response_model=BriefingResponse)
def get_briefing(briefing_id: UUID, db: Session = Depends(get_db)):
    briefing = db.query(Briefing).filter(Briefing.id == briefing_id).first()
    if not briefing:
        raise HTTPException(status_code=404, detail="Briefing not found")
    return briefing


@router.delete("/{briefing_id}", status_code=204)
def delete_briefing(briefing_id: UUID, db: Session = Depends(get_db)):
    briefing = db.query(Briefing).filter(Briefing.id == briefing_id).first()
    if not briefing:
        raise HTTPException(status_code=404, detail="Briefing not found")
    db.delete(briefing)
    db.commit()
