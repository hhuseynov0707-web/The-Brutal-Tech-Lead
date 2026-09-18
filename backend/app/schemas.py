"""Data models shared across the WebSocket protocol."""

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
