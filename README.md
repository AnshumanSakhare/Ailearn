# AI Learning Assistant

An AI-powered learning assistant that processes YouTube videos and PDFs to generate
**flashcards**, **quizzes**, and provides **RAG-based contextual chat**.

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Next.js Frontend (Vercel)              │
│  SourceInput → Flashcards | Quiz | Chat (streaming)       │
└────────────────────────┬─────────────────────────────────┘
                         │ REST / SSE
┌────────────────────────▼─────────────────────────────────┐
│                   FastAPI Backend                         │
│  /process-video   /process-pdf                           │
│  /generate-flashcards  /generate-quiz  /chat             │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────────┐ │
│  │ YouTube  │  │   PDF    │  │    OpenAI GPT-4o        │ │
│  │Transcript│  │ PyMuPDF  │  │  text-embedding-3-small │ │
│  └──────────┘  └──────────┘  └────────────────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │          Supabase pgvector (vecs library)          │  │
│  │   Embeddings stored per session_id collection      │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### Key Design Decisions

| Concern | Choice | Rationale |
|---|---|---|
| Chunking | Token-based (tiktoken), 500 tok / 50 overlap | Preserves semantic boundaries |
| Vector store | Supabase pgvector via `vecs` | No extra infra; branches per session |
| Chat streaming | FastAPI `StreamingResponse` → `fetch` ReadableStream | Low latency token delivery |
| Session state | In-memory dict (swap Redis for multi-worker) | Simple; sufficient for single-instance |
| Flashcard/quiz cache | Stored in session after first generation | Avoids redundant LLM calls |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router), TailwindCSS, TypeScript |
| Backend | Python 3.11, FastAPI, Uvicorn |
| AI | OpenAI `gpt-4o`, `text-embedding-3-small` |
| Vector DB | Supabase `pgvector` via the `vecs` library |
| PDF | PyMuPDF (fitz) |
| YouTube | `youtube-transcript-api`, `pytube` |
| Deployment | Vercel (frontend) + Railway / Fly.io (backend) |

---

## Project Structure

```
ailearn/
├── backend/
│   ├── main.py                # FastAPI app & CORS
│   ├── config.py              # Pydantic settings
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .env.example
│   ├── models/
│   │   └── schemas.py         # Request/response Pydantic models
│   ├── routers/
│   │   ├── video.py           # POST /process-video
│   │   ├── pdf.py             # POST /process-pdf
│   │   ├── flashcards.py      # POST /generate-flashcards
│   │   ├── quiz.py            # POST /generate-quiz  + /evaluate
│   │   └── chat.py            # POST /chat (streaming)
│   └── services/
│       ├── youtube.py         # Transcript extraction
│       ├── pdf.py             # PDF text extraction
│       ├── embeddings.py      # OpenAI embeddings + chunking
│       ├── vector_store.py    # pgvector upsert/query via vecs
│       ├── ai.py              # Flashcard / quiz / RAG chat generation
│       └── session_store.py   # In-memory session metadata
│
├── frontend/
│   ├── next.config.js
│   ├── tailwind.config.ts
│   ├── package.json
│   ├── Dockerfile
│   ├── .env.example
│   └── src/
│       ├── app/
│       │   ├── layout.tsx
│       │   ├── page.tsx       # Main orchestration page
│       │   └── globals.css
│       ├── components/
│       │   ├── Navbar.tsx
│       │   ├── SourceInput.tsx   # YouTube URL / PDF upload
│       │   ├── FlashcardDeck.tsx # Flip card UI
│       │   ├── QuizPanel.tsx     # MCQ + auto-evaluation
│       │   └── ChatBox.tsx       # Streaming RAG chat
│       └── lib/
│           └── api.ts            # Typed fetch wrapper + SSE reader
│
├── supabase_setup.sql         # Enable pgvector extension
├── docker-compose.yml
├── .gitignore
└── README.md
```

---

## Setup Instructions

### Prerequisites

- Node.js 20+
- Python 3.11+
- A [Supabase](https://supabase.com) project
- An [OpenAI](https://platform.openai.com) account

### 1. Supabase – Enable pgvector

Open **SQL Editor** in your Supabase dashboard and run:

```sql
-- supabase_setup.sql
create extension if not exists vector;
create schema if not exists vecs;
```

### 2. Backend

```bash
cd backend
cp .env.example .env
# Fill in OPENAI_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_DB_URL

python -m venv .venv
# Windows:  .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for the interactive Swagger UI.

### 3. Frontend

```bash
cd frontend
cp .env.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8000

npm install
npm run dev
```

Open `http://localhost:3000`.

### 4. Docker (full stack)

```bash
# From project root
cp backend/.env.example backend/.env   # fill in secrets
cp frontend/.env.example frontend/.env.local

docker compose up --build
```

---

## API Reference

| Method | Endpoint | Body | Description |
|---|---|---|---|
| POST | `/process-video` | `{url, session_id?}` | Fetch YouTube transcript, chunk, embed, store |
| POST | `/process-pdf` | `multipart/form-data file` | Extract PDF text, chunk, embed, store |
| POST | `/generate-flashcards` | `{session_id}` | Generate 12 flashcards (cached) |
| POST | `/generate-quiz` | `{session_id}` | Generate 7 MCQ questions (cached) |
| POST | `/generate-quiz/evaluate` | `{session_id, answers}` | Score answers, return explanations |
| POST | `/chat` | `{session_id, message, history}` | Streaming RAG chat response |
| GET | `/health` | — | Health check |

---

## Deployment

### Frontend → Vercel

```bash
cd frontend
npx vercel --prod
# Set NEXT_PUBLIC_API_URL to your backend URL in Vercel dashboard
```

### Backend → Railway / Fly.io

```bash
# Railway
railway up

# Or Fly.io
flyctl launch
flyctl deploy
```

Set all environment variables from `.env.example` in your hosting provider's dashboard.

---

## Evaluation Criteria Coverage

| Criteria | Implementation |
|---|---|
| Architecture & Code Structure | Layered: routers → services → AI/vector store |
| AI Integration Quality | GPT-4o with structured JSON output + retry logic |
| RAG Implementation | pgvector similarity search → injected context → streaming response |
| Flashcard & Quiz Logic | JSON-schema generation, server-side quiz evaluation |
| UI/UX & Responsiveness | TailwindCSS dark theme, flip cards, streaming chat bubbles |
| Error Handling | HTTP exceptions, toast notifications, fallback chunk retrieval |
| Documentation | This README + inline docstrings + `/docs` Swagger UI |
