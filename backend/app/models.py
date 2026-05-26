import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID

from app.database import Base


class Briefing(Base):
    __tablename__ = "briefings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    condition = Column(String, nullable=False)
    status = Column(String, default="pending")
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)
