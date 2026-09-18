"""FastAPI entrypoint: health check, CV upload, text-to-speech and the interview WebSocket."""

import asyncio
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, Query, Request, Response, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from .agent import AgentError, TechLeadAgent
from .config import get_settings
from .cv import MAX_UPLOAD_BYTES, CVError, ProfileStore, load_cv, normalize_text
from .questions import pick_opening_question
from .schemas import CandidateProfile, ClientMessage, CVUploadResponse, Language, MessageType, ServerMessage, TTSRequest
from .session import InterviewSession
from .tts import TTSError, synthesize

settings = get_settings()
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
)
logger = logging.getLogger("brutal_tech_lead")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.profiles = ProfileStore()
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
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, object]:
    return {"status": "ok", "agent_ready": app.state.agent is not None, "model": settings.groq_model}


@app.post("/cv", response_model=CVUploadResponse)
async def upload_cv(request: Request, file: UploadFile = File(...)) -> CVUploadResponse:
    """Extract a CV's text, let the agent build a profile, and keep it for the interview."""
    agent: TechLeadAgent | None = request.app.state.agent
    if agent is None:
        raise HTTPException(status_code=503, detail="Server konfiqurasiya olunmayıb: GROQ_API_KEY tapılmadı.")

    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Fayl 5 MB-dan böyük ola bilməz.")

    try:
        document = await asyncio.to_thread(load_cv, file.filename or "", data, settings.ocr_max_pages)
        if document.needs_ocr:
            logger.info("No text layer found, running OCR on %d page(s)", len(document.images))
            try:
                text = normalize_text(await agent.transcribe_images(document.images))
            except AgentError as exc:
                logger.warning("OCR failed: %s", exc)
                raise HTTPException(status_code=502, detail="Skan edilmiş CV oxuna bilmədi. Bir az sonra yenidən cəhd et.") from exc
        else:
            text = normalize_text(document.text)
    except CVError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    try:
        profile = await agent.analyze_cv(text)
    except AgentError as exc:
        logger.warning("CV analysis failed: %s", exc)
        raise HTTPException(status_code=502, detail="CV analiz edilə bilmədi. Bir az sonra yenidən cəhd et.") from exc

    if not profile.is_cv:
        raise HTTPException(status_code=422, detail="Bu sənəd texniki CV kimi tanınmadı.")

    cv_id = request.app.state.profiles.put(profile)
    logger.info("CV analysed (role=%r, seniority=%r)", profile.target_role, profile.seniority)
    return CVUploadResponse(cv_id=cv_id, profile=profile)


async def _opening_question(agent: TechLeadAgent, role: str, profile: CandidateProfile | None, lang: str | None) -> str:
    """Tailored first question from the agent; the static question bank is the fallback."""
    if settings.enable_scraper and profile is None:
        return await pick_opening_question(role, use_scraper=True)
    try:
        return await agent.opening_question(profile or CandidateProfile(target_role=role), lang)
    except AgentError as exc:
        logger.warning("Opening question generation failed, using question bank: %s", exc)
    return await pick_opening_question(role)


@app.post("/tts", response_class=Response, responses={200: {"content": {"audio/mpeg": {}}}})
async def text_to_speech(request: TTSRequest) -> Response:
    try:
        audio = await synthesize(request.text, request.lang)
    except TTSError as exc:
        logger.warning("%s", exc)
        raise HTTPException(status_code=502, detail="Text-to-speech is unavailable") from exc
    return Response(content=audio, media_type="audio/mpeg", headers={"Cache-Control": "no-store"})


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
async def interview_websocket(
    websocket: WebSocket,
    role: str | None = Query(default=None, max_length=120),
    cv_id: str | None = Query(default=None, max_length=64),
    lang: Language | None = Query(default=None),
):
    await websocket.accept()
    agent: TechLeadAgent | None = websocket.app.state.agent

    if agent is None:
        await _send(websocket, ServerMessage(
            type=MessageType.ERROR,
            ai_reply="Server konfiqurasiya olunmayıb: GROQ_API_KEY tapılmadı.",
        ))
        await websocket.close(code=1011)
        return

    profile: CandidateProfile | None = None
    if cv_id:
        profile = websocket.app.state.profiles.get(cv_id)
        if profile is None:
            await _send(websocket, ServerMessage(
                type=MessageType.ERROR,
                ai_reply="CV sessiyasının vaxtı bitib. CV-ni yenidən yüklə.",
            ))
            await websocket.close(code=4404)
            return

    role = profile.target_role if profile else (role or settings.interview_role).strip() or settings.interview_role
    first_question = await _opening_question(agent, role, profile, lang)
    session = InterviewSession(
        role=role,
        first_question=first_question,
        system_message=agent.system_prompt(role, profile),
        evaluator=agent.evaluate,
        max_turns=settings.max_turns,
        history_window=settings.history_window,
    )
    logger.info("Interview started (role=%r, from_cv=%s)", role, profile is not None)
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
                replies = await session.answer(message.text, message.lang)
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
