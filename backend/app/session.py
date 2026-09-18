"""Per-connection interview state: history, scores and end-of-interview rules."""

import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from .schemas import Evaluation, MessageType, ServerMessage, Verdict

Evaluator = Callable[[list[dict[str, str]]], Awaitable[Evaluation]]

# Three weak answers in a row and the candidate is shown the door.
FAIL_STREAK = 3
FAIL_THRESHOLD = 30
PASS_THRESHOLD = 60

LANGUAGE_NAMES = {"en-US": "ingilis", "az-AZ": "Azərbaycan", "tr-TR": "türk"}


@dataclass
class InterviewSession:
    role: str
    first_question: str
    system_message: dict[str, str]
    evaluator: Evaluator
    max_turns: int = 8
    history_window: int = 12

    turn: int = 0
    tech_scores: list[int] = field(default_factory=list)
    stress_scores: list[int] = field(default_factory=list)
    finished: bool = False
    _history: list[dict[str, str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._history.append({"role": "assistant", "content": self.first_question})

    def opening_message(self) -> ServerMessage:
        return ServerMessage(
            type=MessageType.QUESTION,
            ai_reply=self.first_question,
            tech_accuracy_score=100,
            stress_level_score=10,
            max_turns=self.max_turns,
        )

    def _context(self) -> list[dict[str, str]]:
        return [self.system_message, *self._history[-self.history_window :]]

    async def answer(self, text: str, lang: str | None = None) -> list[ServerMessage]:
        """Evaluate a candidate answer and return the messages to send back.

        `lang` is the UI voice language; the reply is requested in it so the
        text-to-speech voice matches what it has to read.
        """
        if self.finished:
            return []

        content = f"Namizədin cavabı: {text}"
        if lang in LANGUAGE_NAMES:
            content += f'\n\n("response" sahəsini yalnız {LANGUAGE_NAMES[lang]} dilində yaz.)'
        self._history.append({"role": "user", "content": content})
        try:
            evaluation = await self.evaluator(self._context())
        except Exception:
            # Keep history consistent so the candidate can simply try again.
            self._history.pop()
            raise

        self._history.append({"role": "assistant", "content": json.dumps(evaluation.model_dump(), ensure_ascii=False)})
        self.turn += 1
        self.tech_scores.append(evaluation.tech_score)
        self.stress_scores.append(evaluation.stress_score)

        messages = [
            ServerMessage(
                type=MessageType.EVALUATION,
                ai_reply=evaluation.response,
                tech_accuracy_score=evaluation.tech_score,
                stress_level_score=evaluation.stress_score,
                turn=self.turn,
                max_turns=self.max_turns,
            )
        ]
        if self._should_end():
            messages.append(self._final_message())
        return messages

    def _should_end(self) -> bool:
        recent = self.tech_scores[-FAIL_STREAK:]
        failed_streak = len(recent) == FAIL_STREAK and all(s < FAIL_THRESHOLD for s in recent)
        return failed_streak or self.turn >= self.max_turns

    def _final_message(self) -> ServerMessage:
        self.finished = True
        avg_tech = round(sum(self.tech_scores) / len(self.tech_scores))
        avg_stress = round(sum(self.stress_scores) / len(self.stress_scores))
        hired = avg_tech >= PASS_THRESHOLD and self.turn >= self.max_turns

        if hired:
            reply = f"Müsahibə bitdi. Orta texniki bal: {avg_tech}%. Təəccüblüdür, amma keçdin. Pazar ertəsi işə başla."
        else:
            reply = f"Müsahibə bitdi. Orta texniki bal: {avg_tech}%. Bu səviyyə ilə komandaya qəbul edə bilmərəm."

        return ServerMessage(
            type=MessageType.END,
            ai_reply=reply,
            tech_accuracy_score=avg_tech,
            stress_level_score=avg_stress,
            turn=self.turn,
            max_turns=self.max_turns,
            verdict=Verdict.HIRED if hired else Verdict.REJECTED,
        )
