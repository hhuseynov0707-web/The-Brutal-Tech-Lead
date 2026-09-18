"""Application settings loaded from environment variables / `.env`."""

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# backend/.env — real environment variables take precedence.
load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _list(value: str | None, default: list[str]) -> list[str]:
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    groq_vision_model: str = "qwen/qwen3.8-27b"
    ocr_max_pages: int = 4
    interview_role: str = "AI Engineer"
    max_turns: int = 8
    history_window: int = 12
    cors_origins: list[str] = field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )
    enable_scraper: bool = False
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Settings":
        defaults = cls()
        return cls(
            groq_api_key=os.getenv("GROQ_API_KEY", "").strip(),
            groq_model=os.getenv("GROQ_MODEL", defaults.groq_model),
            groq_vision_model=os.getenv("GROQ_VISION_MODEL", defaults.groq_vision_model),
            ocr_max_pages=int(os.getenv("OCR_MAX_PAGES", defaults.ocr_max_pages)),
            interview_role=os.getenv("INTERVIEW_ROLE", defaults.interview_role),
            max_turns=int(os.getenv("MAX_TURNS", defaults.max_turns)),
            history_window=int(os.getenv("HISTORY_WINDOW", defaults.history_window)),
            cors_origins=_list(os.getenv("CORS_ORIGINS"), defaults.cors_origins),
            enable_scraper=_bool(os.getenv("ENABLE_SCRAPER"), defaults.enable_scraper),
            log_level=os.getenv("LOG_LEVEL", defaults.log_level).upper(),
        )


@lru_cache
def get_settings() -> Settings:
    return Settings.from_env()
