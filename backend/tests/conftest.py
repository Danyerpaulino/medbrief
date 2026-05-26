import os
import uuid
from datetime import datetime, timezone

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")


class FakeQuery:
    def __init__(self, records):
        self.records = records
        self.target_id = None

    def order_by(self, *_args, **_kwargs):
        return self

    def filter(self, criterion):
        right = getattr(criterion, "right", None)
        self.target_id = getattr(right, "value", None)
        return self

    def first(self):
        return self.records.get(self.target_id)

    def all(self):
        return sorted(
            self.records.values(),
            key=lambda briefing: briefing.created_at,
            reverse=True,
        )


class FakeSession:
    def __init__(self):
        self.records = {}
        self.commits = 0

    def add(self, briefing):
        if briefing.id is None:
            briefing.id = uuid.uuid4()
        if briefing.status is None:
            briefing.status = "pending"
        if briefing.created_at is None:
            briefing.created_at = datetime.now(timezone.utc)
        self.records[briefing.id] = briefing

    def commit(self):
        self.commits += 1

    def refresh(self, _briefing):
        return None

    def query(self, _model):
        return FakeQuery(self.records)

    def delete(self, briefing):
        self.records.pop(briefing.id, None)

    def close(self):
        return None


@pytest.fixture
def api_session():
    return FakeSession()
