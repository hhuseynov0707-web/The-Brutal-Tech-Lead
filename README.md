# The Brutal Tech-Lead

Sərt Tech-Lead ilə real vaxtda texniki **stress müsahibəsi** simulyatoru. Namizəd CV-sini yükləyir — agent sahəni, səviyyəni və layihələri analiz edib müsahibəni məhz o profilə uyğun qurur (Android, Backend, Data, DevOps və s.). Namizəd yazılı və ya səsli cavab verir, LLM agent (Groq) cavabı qiymətləndirir, tənqid edir və növbəti, daha çətin sualı verir. Texniki dəqiqlik və stres səviyyəsi canlı göstərilir; müsahibə sonunda **qəbul / rədd** qərarı verilir.

## Xüsusiyyətlər

- **CV-yə əsaslanan müsahibə** — PDF / DOCX / TXT yüklə; agent hədəf rolu, səviyyəni, bacarıqları, layihələri və yoxlanılacaq mövzuları çıxarır, ilk sualı birbaşa CV-dəki layihədən verir və CV-dəki iddiaları yoxlayır
- CV-siz rejim — istənilən rolu yazıb başlamaq olar
- **Real vaxt WebSocket** əlaqəsi, avtomatik yenidən qoşulma (exponential backoff)
- **Kontekstli agent** — söhbət tarixçəsini xatırlayır, əvvəlki cavablara əsasən sual verir
- **Təbii səs** — Microsoft Edge neural səsləri ilə TTS (`edge-tts`, pulsuz, API açarı lazım deyil); işləməsə brauzer səsinə keçir
- **Səsli rejim** — Speech-to-Text (mikrofon), EN / AZ / TR dil seçimi; agent seçilmiş dildə cavab verir, səssiz rejim
- **Müsahibə qaydaları** — maksimum raund sayı, ard-arda 3 zəif cavabda erkən rədd
- **Rol üzrə sual bankı**, istəyə bağlı Selenium scraper
- Konfiqurasiya `.env` ilə, API açarları kodda deyil
- Backend testləri (pytest), frontend lint (oxlint)

## Arxitektura

```
brutal-tech-lead/
├── backend/                  FastAPI + Groq
│   ├── app/
│   │   ├── main.py           HTTP /health, POST /cv, POST /tts + WebSocket /ws/interview
│   │   ├── cv.py             CV mətninin çıxarılması + müvəqqəti profil yaddaşı
│   │   ├── config.py         .env-dən ayarlar
│   │   ├── agent.py          Groq LLM agenti: CV analizi, açılış sualı, qiymətləndirmə
│   │   ├── session.py        Müsahibə vəziyyəti: tarixçə, ballar, bitmə qaydaları
│   │   ├── questions.py      Açılış sualları (sual bankı)
│   │   ├── tts.py            edge-tts neural səs sintezi
│   │   ├── scraper.py        İstəyə bağlı Selenium scraper
│   │   └── schemas.py        Pydantic modelləri (protokol)
│   └── tests/
└── frontend/                 React 19 + Vite + Tailwind CSS v4
    └── src/
        ├── App.jsx
        ├── config.js
        ├── api.js            CV yükləmə
        ├── components/       SetupScreen, ProfileCard, InterviewScreen, Header, ScoreCard, ChatWindow, Composer, …
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
| `INTERVIEW_ROLE` | `AI Engineer` | Nə CV, nə də rol göndərilmədikdə default rol |
| `MAX_TURNS` | `8` | Müsahibədə raund sayı |
| `HISTORY_WINDOW` | `12` | Agentə göndərilən son mesaj sayı |
| `CORS_ORIGINS` | `http://localhost:5173,...` | İcazə verilən originlər |
| `ENABLE_SCRAPER` | `false` | Selenium scraper-i aktivləşdirir (Chrome tələb edir) |
| `LOG_LEVEL` | `INFO` | Log səviyyəsi |

**Frontend** (`frontend/.env.local`, bax `frontend/.env.example`):

| Dəyişən | Default |
| --- | --- |
| `VITE_WS_URL` | `ws://127.0.0.1:8003/ws/interview` |
| `VITE_API_URL` | `VITE_WS_URL`-in hostu (`http://127.0.0.1:8003`) |

## CV analizi

`POST /cv` (multipart, sahə adı `file`; PDF / DOCX / TXT / MD, maksimum 5 MB) →

```json
{
  "cv_id": "…",
  "profile": {
    "target_role": "Android Developer (Kotlin)",
    "seniority": "senior",
    "years_experience": 7,
    "skills": ["Kotlin", "Jetpack Compose", "…"],
    "projects": ["…"],
    "focus_areas": ["Kotlin Coroutines və Flow-da error handling", "…"],
    "summary": "…"
  }
}
```

Məxfilik: fayl diskə yazılmır, xam CV mətni saxlanılmır — yalnız çıxarılmış profil 2 saat müddətinə yaddaşda qalır. CV mətni analiz üçün Groq API-yə göndərilir. Skan edilmiş (şəkil) PDF-lərdən mətn çıxarıla bilmir.

## WebSocket protokolu

`ws://<host>/ws/interview?cv_id=<id>&lang=az-AZ` — CV ilə
`ws://<host>/ws/interview?role=<rol>&lang=en-US` — CV-siz

Client → server:

```json
{ "type": "answer", "text": "Namizədin cavabı", "lang": "az-AZ" }
```

`lang` (`en-US` | `az-AZ` | `tr-TR`) istəyə bağlıdır — agent cavabı həmin dildə yazır.

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

## Text-to-Speech

`POST /tts` → `audio/mpeg`

```json
{ "text": "Cavabın səthidir.", "lang": "az-AZ" }
```

| Dil | Səs |
| --- | --- |
| `en-US` | `en-US-ChristopherNeural` |
| `az-AZ` | `az-AZ-BabekNeural` |
| `tr-TR` | `tr-TR-AhmetNeural` |

Səslər, sürət və ton `backend/app/tts.py` faylında dəyişdirilə bilər (`edge-tts --list-voices` bütün səsləri göstərir).
`edge-tts` Microsoft-un rəsmi olmayan servisindən istifadə edir — tədris/şəxsi layihələr üçün uyğundur, kommersiya üçün etibarlı deyil.

## Testlər

```bash
cd backend && python -m pytest
cd frontend && npm run lint && npm run build
```
