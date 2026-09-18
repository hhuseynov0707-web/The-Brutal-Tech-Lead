# The Brutal Tech-Lead

Sərt Tech-Lead ilə real vaxtda texniki **stress müsahibəsi** simulyatoru. Namizəd yazılı və ya səsli cavab verir, LLM agent (Groq) cavabı qiymətləndirir, tənqid edir və növbəti, daha çətin sualı verir. Texniki dəqiqlik və stres səviyyəsi canlı göstərilir; müsahibə sonunda **qəbul / rədd** qərarı verilir.

## Xüsusiyyətlər

- **Real vaxt WebSocket** əlaqəsi, avtomatik yenidən qoşulma (exponential backoff)
- **Kontekstli agent** — söhbət tarixçəsini xatırlayır, əvvəlki cavablara əsasən sual verir
- **Səsli rejim** — Speech-to-Text (mikrofon) və Text-to-Speech (EN / AZ / TR), səssiz rejim
- **Müsahibə qaydaları** — maksimum raund sayı, ard-arda 3 zəif cavabda erkən rədd
- **Rol üzrə sual bankı**, istəyə bağlı Selenium scraper
- Konfiqurasiya `.env` ilə, API açarları kodda deyil
- Backend testləri (pytest), frontend lint (oxlint)

## Arxitektura

```
brutal-tech-lead/
├── backend/                  FastAPI + Groq
│   ├── app/
│   │   ├── main.py           HTTP /health + WebSocket /ws/interview
│   │   ├── config.py         .env-dən ayarlar
│   │   ├── agent.py          Groq LLM agenti, JSON cavabın təhlili
│   │   ├── session.py        Müsahibə vəziyyəti: tarixçə, ballar, bitmə qaydaları
│   │   ├── questions.py      Açılış sualları (sual bankı)
│   │   ├── scraper.py        İstəyə bağlı Selenium scraper
│   │   └── schemas.py        Pydantic modelləri (protokol)
│   └── tests/
└── frontend/                 React 19 + Vite + Tailwind CSS v4
    └── src/
        ├── App.jsx
        ├── config.js
        ├── components/       Header, ScoreCard, ProgressCard, ChatWindow, Composer, VerdictBanner
        └── hooks/            useInterview, useReconnectingSocket, useSpeech
```

## Quraşdırma

Tələblər: **Python 3.11+**, **Node.js 20+**, [Groq API açarı](https://console.groq.com/keys).

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install -r requirements-dev.txt
copy .env.example .env         # macOS/Linux: cp .env.example .env
```

`.env` faylında `GROQ_API_KEY` dəyərini doldurun, sonra:

```bash
uvicorn app.main:app --reload --port 8003
```

Yoxlama: <http://127.0.0.1:8003/health> → `{"status": "ok", "agent_ready": true, ...}`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Brauzerdə <http://localhost:5173> açın. Səs funksiyaları üçün Chrome və ya Edge tövsiyə olunur.

## Konfiqurasiya

**Backend** (`backend/.env`):

| Dəyişən | Default | Təsvir |
| --- | --- | --- |
| `GROQ_API_KEY` | — | **Məcburi.** Groq API açarı |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | İstifadə olunan model |
| `INTERVIEW_ROLE` | `AI Engineer` | Client rol göndərmədikdə default rol |
| `MAX_TURNS` | `8` | Müsahibədə raund sayı |
| `HISTORY_WINDOW` | `12` | Agentə göndərilən son mesaj sayı |
| `CORS_ORIGINS` | `http://localhost:5173,...` | İcazə verilən originlər |
| `ENABLE_SCRAPER` | `false` | Selenium scraper-i aktivləşdirir (Chrome tələb edir) |
| `LOG_LEVEL` | `INFO` | Log səviyyəsi |

**Frontend** (`frontend/.env.local`, bax `frontend/.env.example`):

| Dəyişən | Default |
| --- | --- |
| `VITE_WS_URL` | `ws://127.0.0.1:8003/ws/interview` |
| `VITE_INTERVIEW_ROLE` | `AI Engineer` |

## WebSocket protokolu

`ws://<host>/ws/interview?role=<rol>`

Client → server:

```json
{ "type": "answer", "text": "Namizədin cavabı" }
```

Server → client:

```json
{
  "type": "question | evaluation | error | end",
  "ai_reply": "Tech-Lead-in cavabı",
  "tech_accuracy_score": 55,
  "stress_level_score": 30,
  "turn": 1,
  "max_turns": 8,
  "verdict": "hired | rejected | null"
}
```

## Testlər

```bash
cd backend && python -m pytest
cd frontend && npm run lint && npm run build
```
