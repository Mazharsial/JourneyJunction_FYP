<p align="center"><img src="frontend/public/brand/journeyjunction-logo.svg" width="320" alt="Journey Junction"></p>

<h1 align="center">Journey Junction</h1>
<p align="center">AI-powered smart travel planning &amp; document verification platform.</p>

---

Journey Junction lets a traveller enter a destination and instantly receive **flights, hotels, budget-aware
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
| AI | Google Gemini 2.5 Flash (chat + vision OCR) |
| Flights | Travelpayouts / Aviasales (free) + mock fallback |
| Hotels | Geoapify Places (free) + mock fallback |
| Payments | Stripe (test mode) |
| Email / Messaging | Klaviyo · Meta WhatsApp Cloud API |
| DevOps | Docker · docker-compose · GitHub Actions |

## Project layout

```
backend/      FastAPI app, tests, Dockerfile, Alembic migrations
frontend/     Next.js app (App Router, src/)
docs/         ARCHITECTURE, DATABASE, SECURITY, ENVIRONMENT, ROADMAP
docker-compose.yml   Full local stack
PROJECT_CONTEXT.md   Living single-source-of-truth for continuity/recovery
```

## Running the project

Open the folder in **VS Code** or **Kiro**, then use its integrated terminal. The app runs fully
on **mock data** with no API keys — add keys to `.env` later to switch any service to live.

### Option A — Docker (recommended: one command) ⭐
Requires Docker Desktop (with the WSL 2 backend on Windows). That's the only prerequisite —
no Python, Node, or database to install.

1. Open the project folder in **VS Code** or **Kiro**.
2. Make sure `.env` exists (first time only): in the terminal run `copy .env.example .env`.
3. Start everything — pick either:
   - **One click:** `Terminal → Run Task… → Run app (Docker)` (or press `Ctrl+Shift+B`), **or**
   - **One command** in the terminal:
     ```bash
     docker compose up --build
     ```

Then open **http://localhost:3000** (API docs at **http://localhost:8000/docs**). Sign in with the
seeded super admin **`admin@journeyjunction.app` / `Admin@12345`**, or register a new account.

Compose starts PostgreSQL + Redis, runs the migrations and seed automatically, then the API, worker
and frontend — all live-reload on code changes. Stop with `Ctrl+C` (or the **Stop app** task).
Wipe the database for a fresh start with the **Reset database** task (`docker compose down -v`).
The app runs on mock data by default; add keys to `.env` to make any service live.

### Option B — Manual, no Docker (SQLite, two terminals)
No PostgreSQL needed — it uses a local SQLite file.

**Terminal 1 — Backend** (PowerShell on Windows):
```powershell
cd backend
python -m venv .venv                 # first time only
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt      # first time only
$env:DATABASE_URL = "sqlite+aiosqlite:///./dev.db"
$env:APP_ENV = "development"
$env:CORS_ORIGINS = "http://localhost:3000"
# one-time: create tables + seed reference data + a super admin
$env:SUPERUSER_EMAIL = "admin@journeyjunction.app"
$env:SUPERUSER_PASSWORD = "Admin@12345"
python -m scripts.dev_seed
# run the API (keep this terminal open)
uvicorn app.main:app --reload --port 8000
```
(macOS/Linux: use `source .venv/bin/activate` and `export VAR=value` instead of `$env:`.)

**Terminal 2 — Frontend:**
```powershell
cd frontend
npm install                          # first time only
$env:NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000/api/v1"
npm run dev
```
Open **http://localhost:3000** and sign in with the super admin above
(`admin@journeyjunction.app` / `Admin@12345`), or register a new account.

**Run the tests:**
```powershell
cd backend
$env:APP_ENV = "testing"
pytest                               # 95 tests, uses in-memory SQLite
```

## Security & secrets
Secrets live **only** in `.env` (never committed). See `.env.example` for the full list and
`docs/SECURITY.md` for the security architecture. Passport/visa uploads are treated as sensitive PII
(encrypted at rest, short retention, auto-deleted).

## Status
See `PROJECT_CONTEXT.md` → **CURRENT PROJECT STATE** for the live phase tracker.
