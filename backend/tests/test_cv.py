import io

import pytest
from docx import Document

from app.cv import CVError, ProfileStore, load_cv
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


def _scanned_pdf_bytes(pages: int = 2) -> bytes:
    """A PDF made only of images — no text layer, like a scanner produces."""
    from PIL import Image

    images = [Image.new("RGB", (600, 800), "white") for _ in range(pages)]
    buffer = io.BytesIO()
    images[0].save(buffer, "PDF", save_all=True, append_images=images[1:])
    return buffer.getvalue()


def _png_bytes() -> bytes:
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (3000, 1500), "white").save(buffer, "PNG")
    return buffer.getvalue()


def test_extracts_txt_and_docx():
    assert "Kafka" in load_cv("cv.txt", CV_TEXT.encode()).text
    assert "settlement pipeline" in load_cv("cv.DOCX", _docx_bytes(CV_TEXT)).text


def test_scanned_pdf_is_rendered_for_ocr():
    document = load_cv("scan.pdf", _scanned_pdf_bytes(pages=6), max_ocr_pages=4)
    assert document.needs_ocr
    assert len(document.images) == 4
    assert all(image.startswith(bytes([0xFF, 0xD8, 0xFF])) for image in document.images)  # JPEG


def test_photo_is_downscaled_jpeg():
    from PIL import Image

    document = load_cv("photo.PNG", _png_bytes())
    assert document.needs_ocr and len(document.images) == 1
    with Image.open(io.BytesIO(document.images[0])) as image:
        assert image.format == "JPEG" and max(image.size) <= 2000


@pytest.mark.parametrize(
    ("name", "data"),
    [("cv.exe", b"MZ"), ("cv.txt", b"too short"), ("cv.pdf", b"not a pdf"), ("cv", CV_TEXT.encode()), ("cv.jpg", b"nope")],
)
def test_rejects_bad_files(name, data):
    with pytest.raises(CVError):
        load_cv(name, data)


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


def test_upload_scanned_pdf_uses_ocr(client, fake_agent):
    resp = client.post("/cv", files={"file": ("scan.pdf", _scanned_pdf_bytes(), "application/pdf")})
    assert resp.status_code == 200
    assert fake_agent.ocr_pages == 2
    assert "Kafka" in fake_agent.analyzed[0]


def test_upload_photo_uses_ocr(client, fake_agent):
    resp = client.post("/cv", files={"file": ("cv.jpg", _png_bytes(), "image/jpeg")})
    assert resp.status_code == 200 and fake_agent.ocr_pages == 1


def test_ocr_failure_and_empty_ocr(client, fake_agent):
    from app.agent import AgentError

    async def broken(images):
        raise AgentError("vision down")

    fake_agent.transcribe_images = broken
    assert client.post("/cv", files={"file": ("scan.pdf", _scanned_pdf_bytes(), "application/pdf")}).status_code == 502

    async def blank(images):
        return ""

    fake_agent.transcribe_images = blank
    assert client.post("/cv", files={"file": ("scan.pdf", _scanned_pdf_bytes(), "application/pdf")}).status_code == 422
