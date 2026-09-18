"""The Brutal Tech-Lead: an LLM agent that grills the candidate."""

import json
import logging
import re

from groq import AsyncGroq
from pydantic import ValidationError

from .config import Settings
from .schemas import Evaluation

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
Sən təcrübəli, olduqca tələbkar və sərt bir Tech-Lead-sən (Baş Mühəndis).
Vəzifə: "{role}" pozisiyası üçün texniki müsahibə aparırsan.

Qaydalar:
- Namizədin hər cavabını texniki dəqiqlik baxımından qiymətləndir.
- Zəif yerləri açıq və sərt şəkildə göstər, amma təhqir etmə.
- Hər cavabın sonunda əvvəlki mövzunu dərinləşdirən və ya yeni, daha çətin bir sual ver.
- Namizəd hansı dildə yazırsa, həmin dildə cavab ver.
- Cavab qısa olsun (maksimum 4-5 cümlə) — o, səsləndiriləcək.

Cavabın YALNIZ bu JSON formatında olmalıdır, markdown və ya əlavə mətn olmadan:
{{
  "response": "Sərt tənqidi rəy + növbəti çətin sual",
  "tech_score": <0-100 arası tam ədəd, cavabın texniki dəqiqliyi>,
  "stress_score": <0-100 arası tam ədəd, namizədin cavabından hiss olunan stres səviyyəsi>
}}
"""

_CODE_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


class AgentError(RuntimeError):
    """Raised when the agent cannot produce a valid evaluation."""


def parse_evaluation(raw: str) -> Evaluation:
    """Extract and validate the JSON evaluation from a raw model reply."""
    content = raw.strip()

    fenced = _CODE_FENCE.search(content)
    if fenced:
        content = fenced.group(1).strip()

    # Fall back to the outermost {...} block if the model added prose around it.
    if not content.startswith("{"):
        start, end = content.find("{"), content.rfind("}")
        if start != -1 and end > start:
            content = content[start : end + 1]

    try:
        return Evaluation.model_validate(json.loads(content))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise AgentError(f"Model returned an invalid evaluation: {raw[:200]!r}") from exc


class TechLeadAgent:
    """Stateless wrapper around the Groq client; history is passed per call."""

    def __init__(self, settings: Settings):
        if not settings.groq_api_key:
            raise AgentError("GROQ_API_KEY is not set. Copy .env.example to .env and fill it in.")
        self._settings = settings
        self._client = AsyncGroq(api_key=settings.groq_api_key)

    def system_prompt(self, role: str) -> dict[str, str]:
        return {"role": "system", "content": SYSTEM_PROMPT.format(role=role)}

    async def evaluate(self, messages: list[dict[str, str]]) -> Evaluation:
        try:
            completion = await self._client.chat.completions.create(
                model=self._settings.groq_model,
                messages=messages,
                temperature=1,
                max_completion_tokens=2048,
                top_p=1,
                reasoning_effort="medium",
                stream=False,
            )
        except Exception as exc:  # network / auth / rate-limit errors from the SDK
            raise AgentError(f"Groq request failed: {exc}") from exc

        content = completion.choices[0].message.content or ""
        return parse_evaluation(content)
