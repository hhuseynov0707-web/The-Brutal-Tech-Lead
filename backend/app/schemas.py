"""Data models shared across the HTTP API and the WebSocket protocol."""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


def _clamp_score(value: object) -> int:
    try:
        number = int(round(float(value)))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 50
    return max(0, min(100, number))


class Evaluation(BaseModel):
    """A single judgement produced by the Tech-Lead agent."""

    response: str = Field(min_length=1)
    tech_score: int = 50
    stress_score: int = 50

    @field_validator("tech_score", "stress_score", mode="before")
    @classmethod
    def clamp(cls, value: object) -> int:
        return _clamp_score(value)


def _short_list(value: object, max_items: int, max_len: int = 120) -> list[str]:
    if not isinstance(value, list):
        return []
    items = [str(v).strip()[:max_len] for v in value if str(v).strip()]
    return items[:max_items]


class CandidateProfile(BaseModel):
    """Structured summary of a CV, produced by the agent."""

    is_cv: bool = True
    name: str | None = Field(default=None, max_length=80)
    target_role: str = Field(default="Software Engineer", max_length=120)
    seniority: str = Field(default="junior", max_length=30)
    years_experience: float | None = Field(default=None, ge=0, le=60)
    skills: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    focus_areas: list[str] = Field(default_factory=list)
    summary: str = Field(default="", max_length=600)

    @field_validator("skills", mode="before")
    @classmethod
    def _skills(cls, value: object) -> list[str]:
        return _short_list(value, 20, 60)

    @field_validator("projects", "focus_areas", mode="before")
    @classmethod
    def _lists(cls, value: object) -> list[str]:
        return _short_list(value, 6, 200)

    @field_validator("name", "summary", "target_role", "seniority", mode="before")
    @classmethod
    def _truncate(cls, value: object, info) -> object:
        limits = {"name": 80, "summary": 600, "target_role": 120, "seniority": 30}
        return value.strip()[: limits[info.field_name]] if isinstance(value, str) else value

    @field_validator("years_experience", mode="before")
    @classmethod
    def _years(cls, value: object) -> float | None:
        try:
            return max(0.0, min(60.0, float(value)))  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return None

    def as_prompt(self) -> str:
        """Compact, human-readable block for the interviewer's system prompt."""
        lines = [
            f"- Hədəf rol: {self.target_role}",
            f"- Səviyyə: {self.seniority}"
            + (f" (~{self.years_experience:g} il təcrübə)" if self.years_experience is not None else ""),
        ]
        if self.skills:
            lines.append(f"- Bacarıqlar: {', '.join(self.skills)}")
        if self.projects:
            lines.append("- Layihələr:\n" + "\n".join(f"  • {p}" for p in self.projects))
        if self.focus_areas:
            lines.append(f"- Yoxlanılacaq mövzular: {'; '.join(self.focus_areas)}")
        if self.summary:
            lines.append(f"- Xülasə: {self.summary}")
        return "\n".join(lines)


class CVUploadResponse(BaseModel):
    cv_id: str
    profile: CandidateProfile


class MessageType(str, Enum):
    QUESTION = "question"
    EVALUATION = "evaluation"
    ERROR = "error"
    END = "end"


class Verdict(str, Enum):
    HIRED = "hired"
    REJECTED = "rejected"


class ServerMessage(BaseModel):
    """Payload sent from the server to the client."""

    type: MessageType
    ai_reply: str
    tech_accuracy_score: int | None = None
    stress_level_score: int | None = None
    turn: int = 0
    max_turns: int = 0
    verdict: Verdict | None = None


Language = Literal["en-US", "az-AZ", "tr-TR"]


class ClientMessage(BaseModel):
    """Payload sent from the client to the server."""

    type: str = "answer"
    text: str = Field(min_length=1, max_length=4000)
    lang: Language | None = None


class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    lang: Language = "en-US"
