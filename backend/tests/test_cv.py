import io

import pytest
from docx import Document

from app.cv import CVError, ProfileStore, extract_text
from app.schemas import CandidateProfile

CV_TEXT = (
    "Aysel Mammadova — Backend Engineer\n"
    "5 years of experience building payment systems in Go and PostgreSQL.\n"
    "Designed an event-driven settlement pipeline on Kafka processing 2k rps.\n"
    "Skills: Go, PostgreSQL, Kafka, Docker, Kubernetes, gRPC, Redis.\n"
)


def _docx_bytes(text: str) -> bytes:
    document = Document()
    for line in text.splitlines():
        document.add_paragraph(line)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def test_extracts_txt_and_docx():
    assert "Kafka" in extract_text("cv.txt", CV_TEXT.encode())
    assert "settlement pipeline" in extract_text("cv.DOCX", _docx_bytes(CV_TEXT))


@pytest.mark.parametrize(
    ("name", "data"),
    [("cv.exe", b"MZ"), ("cv.txt", b"too short"), ("cv.pdf", b"not a pdf"), ("cv", CV_TEXT.encode())],
)
def test_rejects_bad_files(name, data):
    with pytest.raises(CVError):
        extract_text(name, data)


def test_profile_store_expires_and_bounds():
    store = ProfileStore(ttl_seconds=-1)
    cv_id = store.put(CandidateProfile())
    assert store.get(cv_id) is None

    store = ProfileStore(max_items=2)
    ids = [store.put(CandidateProfile()) for _ in range(3)]
    assert store.get(ids[0]) is None and store.get(ids[2]) is not None


def test_profile_normalises_llm_output():
    profile = CandidateProfile.model_validate(
        {"skills": [f"s{i}" for i in range(30)], "years_experience": "7", "projects": "oops", "summary": "x" * 900}
    )
    assert len(profile.skills) == 20
    assert profile.years_experience == 7
    assert profile.projects == []
    assert len(profile.summary) == 600


def test_upload_cv_returns_profile(client, fake_agent):
    resp = client.post("/cv", files={"file": ("cv.txt", CV_TEXT.encode(), "text/plain")})
    assert resp.status_code == 200
    body = resp.json()
    assert body["cv_id"]
    assert body["profile"]["target_role"] == "Backend Engineer (Go)"
    assert "Kafka" in fake_agent.analyzed[0]


def test_upload_rejects_unsupported_and_large_files(client):
    assert client.post("/cv", files={"file": ("cv.png", b"x" * 500, "image/png")}).status_code == 422
    big = b"a" * (5 * 1024 * 1024 + 1)
    assert client.post("/cv", files={"file": ("cv.txt", big, "text/plain")}).status_code == 413


def test_upload_rejects_non_cv(client, fake_agent):
    fake_agent.profile = CandidateProfile(is_cv=False)
    assert client.post("/cv", files={"file": ("cv.txt", CV_TEXT.encode(), "text/plain")}).status_code == 422


def test_interview_uses_cv_profile(client, fake_agent):
    cv_id = client.post("/cv", files={"file": ("cv.txt", CV_TEXT.encode(), "text/plain")}).json()["cv_id"]

    with client.websocket_connect(f"/ws/interview?cv_id={cv_id}&lang=az-AZ") as ws:
        opening = ws.receive_json()
        assert opening["type"] == "question"
        assert opening["ai_reply"].startswith("[az-AZ]")
        assert "Payment service" in opening["ai_reply"]

        ws.send_text('{"type": "answer", "text": "Goroutines and backpressure."}')
        ws.receive_json()
        system = fake_agent.calls[-1][0]["content"]
        assert "Backend Engineer (Go)" in system and "Kafka" in system


def test_unknown_cv_id_is_reported(client):
    with client.websocket_connect("/ws/interview?cv_id=missing") as ws:
        message = ws.receive_json()
        assert message["type"] == "error"
