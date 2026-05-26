import asyncio
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi import BackgroundTasks, HTTPException

from app.models import Briefing
from app.routes import briefings as briefings_module
from app.schemas import BriefingCreate


def test_create_briefing_persists_record_and_schedules_worker(
    api_session, monkeypatch
):
    scheduled = []

    async def fake_run_briefing_agent(briefing_id):
        scheduled.append(briefing_id)

    monkeypatch.setattr(
        briefings_module,
        "run_briefing_agent",
        fake_run_briefing_agent,
    )

    background_tasks = BackgroundTasks()
    briefing = briefings_module.create_briefing(
        BriefingCreate(condition="Type 2 Diabetes"),
        background_tasks,
        api_session,
    )
    asyncio.run(background_tasks())

    assert briefing.condition == "Type 2 Diabetes"
    assert briefing.status == "pending"
    assert briefing.id in api_session.records
    assert scheduled == [briefing.id]


def test_list_and_get_briefings(api_session):
    older = Briefing(condition="Asthma")
    newer = Briefing(condition="Heart Failure")
    api_session.add(older)
    api_session.add(newer)
    older.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    newer.created_at = datetime(2024, 1, 2, tzinfo=timezone.utc)

    briefings = briefings_module.list_briefings(api_session)
    assert [briefing.condition for briefing in briefings] == [
        "Heart Failure",
        "Asthma",
    ]

    briefing = briefings_module.get_briefing(older.id, api_session)
    assert briefing.condition == "Asthma"


def test_get_briefing_returns_404_for_missing_record(api_session):
    with pytest.raises(HTTPException) as exc_info:
        briefings_module.get_briefing(uuid4(), api_session)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Briefing not found"


def test_delete_briefing_removes_record(api_session):
    briefing = Briefing(condition="Migraine")
    api_session.add(briefing)

    result = briefings_module.delete_briefing(briefing.id, api_session)

    assert result is None
    assert briefing.id not in api_session.records
    with pytest.raises(HTTPException):
        briefings_module.get_briefing(briefing.id, api_session)
