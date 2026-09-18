import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import CandidateProfile, Evaluation


class FakeAgent:
    def __init__(self, scores=None):
        self.scores = list(scores or [])
        self.calls: list[list[dict[str, str]]] = []
        self.profile = CandidateProfile(
            target_role="Backend Engineer (Go)",
            seniority="middle",
            skills=["Go", "PostgreSQL", "Kafka"],
            projects=["Payment service handling 2k rps"],
            focus_areas=["Go concurrency"],
        )
        self.analyzed: list[str] = []
        self.ocr_pages = 0

    def system_prompt(self, role: str, profile=None) -> dict[str, str]:
        extra = f" | {profile.as_prompt()}" if profile else ""
        return {"role": "system", "content": f"grill {role}{extra}"}

    async def evaluate(self, messages):
        self.calls.append(messages)
        score = self.scores.pop(0) if self.scores else 70
        return Evaluation(response=f"Reply {len(self.calls)}", tech_score=score, stress_score=40)

    async def transcribe_images(self, images: list[bytes]) -> str:
        from tests.test_cv import CV_TEXT

        self.ocr_pages += len(images)
        return CV_TEXT

    async def analyze_cv(self, text: str) -> CandidateProfile:
        self.analyzed.append(text)
        return self.profile

    async def opening_question(self, profile, lang) -> str:
        subject = profile.projects[0] if profile.projects else profile.target_role
        return f"[{lang}] How did your {subject} survive load?"


@pytest.fixture
def fake_agent():
    return FakeAgent()


@pytest.fixture
def client(fake_agent):
    with TestClient(app) as test_client:
        app.state.agent = fake_agent
        yield test_client
