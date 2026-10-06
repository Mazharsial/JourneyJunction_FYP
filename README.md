<p align="center"><img src="frontend/public/brand/voynixai-logo.svg" width="320" alt="VoynixAI"></p>

<h1 align="center">VoynixAI</h1>
<p align="center">AI-powered smart travel planning &amp; document verification platform.</p>

---

VoynixAI lets a traveller enter a destination and instantly receive **flights, hotels, budget-aware
recommendations and an AI-generated itinerary** — plus its flagship feature: **AI-powered travel
document verification & correction** (OCR + LLM analysis of passports, visa forms and tickets with
compliance checking).

> Final Year Project — Group 12, Superior University (Lahore). Initial market: **Dubai, UAE**
> (fully configurable for future expansion). Formerly branded "Tripzy".

## Tech stack (free / open-source first)

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12 · FastAPI · SQLAlchemy (async) · Alembic |
| Frontend | Next.js 16 · React 19 · TypeScript · Tailwind v4 · Framer Motion |
| Database | PostgreSQL 16 |
| Cache / jobs | Redis · Celery |
| AI | Google Gemini (free tier) |
| OCR | Tesseract / EasyOCR / PaddleOCR (benchmarked) |
| Travel data | Amadeus Self-Service (free test env) + mock fallback |
| Payments | Stripe (test mode) |
| Messaging | Meta WhatsApp Cloud API · Klaviyo |
| DevOps | Docker · docker-compose · GitHub Actions |

## Project layout

```
backend/      FastAPI app, tests, Dockerfile, Alembic migrations
frontend/     Next.js app (App Router, src/)
docs/         ARCHITECTURE, DATABASE, SECURITY, ENVIRONMENT, ROADMAP
docker-compose.yml   Full local stack
PROJECT_CONTEXT.md   Living single-source-of-truth for continuity/recovery
```

## Quick start

### 1. Prerequisites
- Python 3.12, Node 22+, Git (installed)
- **Docker Desktop** (for the full stack): `winget install -e --id Docker.DockerDesktop` then reboot.

### 2. Run everything with Docker (recommended)
```bash
cp .env.example .env     # fill in secrets as phases require them
docker compose up --build
# Frontend  → http://localhost:3000
# API docs  → http://localhost:8000/docs
```

### 3. Run services individually (no Docker)
**Backend**
```bash
cd backend
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload     # needs a reachable PostgreSQL for DB features
pytest                            # foundation tests (no DB required)
```
**Frontend**
```bash
cd frontend
npm install
npm run dev     # http://localhost:3000
```

## Security & secrets
Secrets live **only** in `.env` (never committed). See `.env.example` for the full list and
`docs/SECURITY.md` for the security architecture. Passport/visa uploads are treated as sensitive PII
(encrypted at rest, short retention, auto-deleted).

## Status
See `PROJECT_CONTEXT.md` → **CURRENT PROJECT STATE** for the live phase tracker.
