"""Opening questions: a curated bank, optionally enriched by the live scraper."""

import asyncio
import logging
import random

from .scraper import fetch_interview_topics

logger = logging.getLogger(__name__)

SCRAPER_TIMEOUT = 20

QUESTION_BANK: dict[str, list[str]] = {
    "ai engineer": [
        "Explain why your RAG pipeline returns confidently wrong answers and how you would measure and fix it.",
        "Your LLM endpoint's p99 latency just tripled after a prompt change. Walk me through the debugging.",
        "How do you evaluate an LLM feature before shipping it, when there is no single correct answer?",
        "Explain the trade-offs between fine-tuning, prompt engineering and retrieval for a domain-specific assistant.",
        "What exactly happens to the KV cache during autoregressive decoding, and why does it matter for cost?",
    ],
    "python engineer": [
        "Explain the GIL. When does multi-threading still help in Python, and when is it useless?",
        "Explain how memory leaks occur in asynchronous event loops and how you debug them.",
        "Write a custom decorator that measures execution time and retries on failure. Where does it break?",
        "How do you optimize a SQL query over 10 million rows with zero indexes?",
    ],
}

GENERIC_QUESTIONS = [
    "Why should we hire you for a {role} position if your system fails under load?",
    "Describe the worst production incident you caused and what you changed afterwards.",
    "Design a rate limiter for a public API. Where does your design fall apart?",
]


def _bank_for(role: str) -> list[str]:
    key = role.strip().lower()
    for name, questions in QUESTION_BANK.items():
        if name in key or key in name:
            return questions
    return [q.format(role=role) for q in GENERIC_QUESTIONS]


async def pick_opening_question(role: str, use_scraper: bool = False) -> str:
    candidates: list[str] = []
    if use_scraper:
        try:
            scraped = await asyncio.wait_for(
                asyncio.to_thread(fetch_interview_topics, role), timeout=SCRAPER_TIMEOUT
            )
            candidates.extend(scraped)
        except asyncio.TimeoutError:
            logger.warning("Scraper timed out after %ss", SCRAPER_TIMEOUT)

    return random.choice(candidates or _bank_for(role))
