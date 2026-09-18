"""Neural text-to-speech via Microsoft Edge's online voices (edge-tts, no API key).

Note: edge-tts talks to an unofficial Microsoft endpoint. It can change without
notice, so the frontend falls back to the browser's speechSynthesis on failure.
"""

import logging
from collections import OrderedDict

import edge_tts

logger = logging.getLogger(__name__)

# One voice per supported UI language; ChristopherNeural is tagged "Authority".
VOICES: dict[str, str] = {
    "en-US": "en-US-ChristopherNeural",
    "az-AZ": "az-AZ-BabekNeural",
    "tr-TR": "tr-TR-AhmetNeural",
}
DEFAULT_LANG = "en-US"

# A slightly slower, lower delivery sounds sterner.
RATE = "-5%"
PITCH = "-8Hz"

MAX_TEXT_LENGTH = 2000
_CACHE_SIZE = 64
_cache: OrderedDict[tuple[str, str], bytes] = OrderedDict()


class TTSError(RuntimeError):
    """Raised when speech synthesis fails."""


def voice_for(lang: str) -> str:
    return VOICES.get(lang, VOICES[DEFAULT_LANG])


async def synthesize(text: str, lang: str = DEFAULT_LANG) -> bytes:
    """Return MP3 audio for `text` spoken in `lang`. Recent results are cached."""
    voice = voice_for(lang)
    key = (voice, text)
    if key in _cache:
        _cache.move_to_end(key)
        return _cache[key]

    communicate = edge_tts.Communicate(text, voice, rate=RATE, pitch=PITCH)
    audio = bytearray()
    try:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio.extend(chunk["data"])
    except Exception as exc:  # network errors, service changes, etc.
        raise TTSError(f"edge-tts failed: {exc}") from exc

    if not audio:
        raise TTSError("edge-tts returned no audio")

    _cache[key] = bytes(audio)
    if len(_cache) > _CACHE_SIZE:
        _cache.popitem(last=False)
    return _cache[key]
