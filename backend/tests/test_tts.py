import pytest

from app import main
from app.tts import TTSError, voice_for


def test_voice_mapping_falls_back_to_english():
    assert voice_for("az-AZ") == "az-AZ-BabekNeural"
    assert voice_for("xx-XX") == voice_for("en-US")


def test_tts_returns_mp3(client, monkeypatch):
    calls = []

    async def fake_synthesize(text, lang):
        calls.append((text, lang))
        return b"ID3fake-mp3"

    monkeypatch.setattr(main, "synthesize", fake_synthesize)
    resp = client.post("/tts", json={"text": "Salam", "lang": "az-AZ"})
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "audio/mpeg"
    assert resp.content == b"ID3fake-mp3"
    assert calls == [("Salam", "az-AZ")]


def test_tts_failure_returns_502(client, monkeypatch):
    async def broken(text, lang):
        raise TTSError("down")

    monkeypatch.setattr(main, "synthesize", broken)
    assert client.post("/tts", json={"text": "hi"}).status_code == 502


@pytest.mark.parametrize("payload", [{"text": ""}, {"text": "hi", "lang": "fr-FR"}, {"text": "x" * 2001}])
def test_tts_validates_input(client, payload):
    assert client.post("/tts", json=payload).status_code == 422
