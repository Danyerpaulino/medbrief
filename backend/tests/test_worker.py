import asyncio
from types import SimpleNamespace
from uuid import uuid4

from app import worker


class FakeQuery:
    def __init__(self, briefing):
        self.briefing = briefing

    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        return self.briefing


class FakeSession:
    def __init__(self, briefing):
        self.briefing = briefing
        self.commits = 0
        self.closed = False

    def query(self, _model):
        return FakeQuery(self.briefing)

    def commit(self):
        self.commits += 1

    def close(self):
        self.closed = True


def make_briefing():
    return SimpleNamespace(
        id=uuid4(),
        condition="Asthma",
        status="pending",
        result=None,
        error=None,
        completed_at=None,
    )


def test_run_briefing_agent_marks_completed(monkeypatch):
    briefing = make_briefing()
    session = FakeSession(briefing)

    class FakeGraph:
        async def ainvoke(self, state):
            assert state == {"condition": "Asthma"}
            return {
                "standard_of_care": [{"title": "Care", "content": "...", "references": []}],
                "emerging_treatments": [],
                "key_players": [],
                "summary": "Executive summary",
                "grounding": [{"section": "Care", "claim": "Test", "supported": True, "source_ids": ["PMID:123"]}],
                "confidence_scores": [{"section": "Care", "level": "strong", "source_count": 10, "newest_year": "2025", "oldest_year": "2020", "rationale": "Well supported."}],
            }

    monkeypatch.setattr(worker, "SessionLocal", lambda: session)
    monkeypatch.setattr(worker, "get_graph", lambda: FakeGraph())

    asyncio.run(worker.run_briefing_agent(briefing.id))

    assert briefing.status == "completed"
    assert briefing.result == {
        "standard_of_care": [{"title": "Care", "content": "...", "references": []}],
        "emerging_treatments": [],
        "key_players": [],
        "summary": "Executive summary",
        "grounding": [{"section": "Care", "claim": "Test", "supported": True, "source_ids": ["PMID:123"]}],
        "confidence_scores": [{"section": "Care", "level": "strong", "source_count": 10, "newest_year": "2025", "oldest_year": "2020", "rationale": "Well supported."}],
    }
    assert briefing.completed_at is not None
    assert session.commits == 2
    assert session.closed is True


def test_run_briefing_agent_normalizes_confidence_scores(monkeypatch):
    briefing = make_briefing()
    session = FakeSession(briefing)

    class FakeGraph:
        async def ainvoke(self, _state):
            return {
                "standard_of_care": [],
                "emerging_treatments": [],
                "key_players": [],
                "summary": "Executive summary",
                "grounding": [
                    {
                        "section": "Care",
                        "claim": "Test",
                        "supported": True,
                        "source_ids": "PMID:123",
                    }
                ],
                "confidence_scores": [
                    {
                        "section": "Care",
                        "level": "Strong",
                        "source_count": "10",
                        "newest_year": 2026,
                        "oldest_year": None,
                        "rationale": None,
                    }
                ],
            }

    monkeypatch.setattr(worker, "SessionLocal", lambda: session)
    monkeypatch.setattr(worker, "get_graph", lambda: FakeGraph())

    asyncio.run(worker.run_briefing_agent(briefing.id))

    assert briefing.status == "completed"
    assert briefing.result["grounding"][0]["source_ids"] == ["PMID:123"]
    assert briefing.result["confidence_scores"][0]["level"] == "strong"
    assert briefing.result["confidence_scores"][0]["source_count"] == 10
    assert briefing.result["confidence_scores"][0]["newest_year"] == "2026"
    assert briefing.result["confidence_scores"][0]["oldest_year"] == "N/A"
    assert briefing.result["confidence_scores"][0]["rationale"] == ""


def test_run_briefing_agent_marks_failed_on_error(monkeypatch):
    briefing = make_briefing()
    session = FakeSession(briefing)

    class FailingGraph:
        async def ainvoke(self, _state):
            raise RuntimeError("LLM unavailable")

    monkeypatch.setattr(worker, "SessionLocal", lambda: session)
    monkeypatch.setattr(worker, "get_graph", lambda: FailingGraph())

    asyncio.run(worker.run_briefing_agent(briefing.id))

    assert briefing.status == "failed"
    assert briefing.error == "LLM unavailable"
    assert session.commits == 2
    assert session.closed is True
