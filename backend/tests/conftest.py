import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import Evaluation


class FakeAgent:
    def __init__(self, scores=None):
        self.scores = list(scores or [])
        self.calls: list[list[dict[str, str]]] = []

    def system_prompt(self, role: str) -> dict[str, str]:
        return {"role": "system", "content": f"grill {role}"}

    async def evaluate(self, messages):
        self.calls.append(messages)
        score = self.scores.pop(0) if self.scores else 70
        return Evaluation(response=f"Reply {len(self.calls)}", tech_score=score, stress_score=40)


@pytest.fixture
def fake_agent():
    return FakeAgent()


@pytest.fixture
def client(fake_agent):
    with TestClient(app) as test_client:
        app.state.agent = fake_agent
        yield test_client
