"""FastAPI entrypoint: health check and the interview WebSocket."""

import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from .agent import AgentError, TechLeadAgent
from .config import get_settings
from .questions import pick_opening_question
from .schemas import ClientMessage, MessageType, ServerMessage
from .session import InterviewSession

settings = get_settings()
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
)
logger = logging.getLogger("brutal_tech_lead")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        app.state.agent = TechLeadAgent(settings)
    except AgentError as exc:
        logger.error("%s", exc)
        app.state.agent = None
    yield


app = FastAPI(title="The Brutal Tech-Lead", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, object]:
    return {"status": "ok", "agent_ready": app.state.agent is not None, "model": settings.groq_model}


def _parse_client_message(raw: str) -> ClientMessage:
    """Accept either `{"type": "answer", "text": "..."}` or plain text."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = None
    if isinstance(data, dict):
        return ClientMessage.model_validate(data)
    return ClientMessage(text=raw.strip())


async def _send(websocket: WebSocket, message: ServerMessage) -> None:
    await websocket.send_text(message.model_dump_json())


@app.websocket("/ws/interview")
async def interview_websocket(websocket: WebSocket, role: str | None = Query(default=None, max_length=80)):
    await websocket.accept()
    agent: TechLeadAgent | None = websocket.app.state.agent

    if agent is None:
        await _send(websocket, ServerMessage(
            type=MessageType.ERROR,
            ai_reply="Server konfiqurasiya olunmayıb: GROQ_API_KEY tapılmadı.",
        ))
        await websocket.close(code=1011)
        return

    role = (role or settings.interview_role).strip() or settings.interview_role
    first_question = await pick_opening_question(role, use_scraper=settings.enable_scraper)
    session = InterviewSession(
        role=role,
        first_question=first_question,
        system_message=agent.system_prompt(role),
        evaluator=agent.evaluate,
        max_turns=settings.max_turns,
        history_window=settings.history_window,
    )
    logger.info("Interview started (role=%r)", role)
    await _send(websocket, session.opening_message())

    try:
        while not session.finished:
            raw = await websocket.receive_text()
            try:
                message = _parse_client_message(raw)
            except ValidationError:
                await _send(websocket, ServerMessage(type=MessageType.ERROR, ai_reply="Boş və ya çox uzun cavab göndərilə bilməz."))
                continue

            try:
                replies = await session.answer(message.text)
            except AgentError as exc:
                logger.warning("Agent failure: %s", exc)
                await _send(websocket, ServerMessage(
                    type=MessageType.ERROR,
                    ai_reply="Tech-Lead hazırda cavab verə bilmir. Bir az sonra yenidən cəhd et.",
                ))
                continue

            for reply in replies:
                await _send(websocket, reply)

        logger.info("Interview finished (turns=%d)", session.turn)
        await websocket.close()
    except WebSocketDisconnect:
        logger.info("Candidate disconnected after %d turn(s)", session.turn)
