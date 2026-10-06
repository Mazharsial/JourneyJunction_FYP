# PROJECT_CONTEXT.md — VoynixAI (single source of truth)

> This file is the project's living memory. Anyone (human or AI) should be able to read this +
> the repo + the proposal and continue development without the prior conversation.
> **Keep it updated after every meaningful task.** Never store real secrets here.

---

## CURRENT PROJECT STATE
```
Current Phase:      Phase 6 — AI chatbot (COMPLETE: backend + chat UI)
Current Feature:    Gemini travel assistant + /dashboard/assistant chat UI
Last Completed:     Phase 6 frontend chat UI (/dashboard/assistant); backend d94e79d pushed; 36 tests; eval 100%/100%
Last Successful Test: backend 36/36 pytest; eval 100%/100%; live Gemini verified; frontend build (12 routes)
Last Git Commit:    (pending Phase 6 frontend commit; Phase 6 backend = d94e79d pushed)
Current Branch:     main (develop to be created)
Next Task:          Phase 7 — OCR + document verification/correction (Tesseract/EasyOCR/Gemini-Vision; ≥90% measured)
Blocked By:         Nothing. Gemini key set + verified. Amadeus optional.
Supervisor doc:     docs/VoynixAI_Project_Documentation.docx (FYP SRS/design report; open in Word and press F9 to populate the Table of Contents).
Required Credentials (upcoming): Amadeus (P5), Gemini (P6), Stripe (P9), Meta WhatsApp + Klaviyo (P8)
Known Issues:       npm reported transitive high-severity advisories (to review in P11 hardening)
```

---

## PROJECT IDENTITY
- **Name:** VoynixAI (brand configurable via `BRAND_NAME` / `NEXT_PUBLIC_BRAND_NAME`; formerly "Tripzy"; may change).
- **Purpose:** One-stop AI travel planning + unique AI document verification & correction.
- **Problem:** Trip planning is fragmented, slow, costly; travellers face visa rejections from small document errors; no single platform does end-to-end planning **plus** AI document verification.
- **Target users:** Domestic/international travellers, business travellers, families, first-timers, budget & luxury travellers, people planning without agents.
- **Initial market:** Dubai, UAE — **configurable** (country/city/currency/locale/timezone/visa-rules in DB), designed for UAE→GCC→international expansion without rewrites.
- **Academic:** Group 12, Superior University Lahore; supervisor Sir Talha; 8-week proposal plan.
- **Repo:** https://github.com/Mazharsial/JourneyJunction_FYP.git
- **Build dir:** `C:\Users\HP\Desktop\Journey_Junction_FYP`

## REQUIREMENTS (from proposal + master prompt)
Core travel: destination-based planning · flight search/compare (price, schedule, duration) · hotel search (price, ratings, amenities) · budget tiers (low/medium/luxury).
AI: travel assistant chatbot · personalised recommendations · smart itinerary generation.
Document verification (flagship): upload passport/visa/tickets · OCR extraction · detect spelling/missing/format/mismatch · suggested corrections/auto-fix · visa compliance checking.
Platform (master prompt): auth + RBAC · Stripe subscriptions with enforced entitlements · admin panel · WhatsApp (Meta) · email (Klaviyo) · security (OWASP, encryption, GDPR/UAE-PDPL) · logging/audit · CI/CD · Docker · tests · docs · **measured** ≥90% chatbot & OCR accuracy.

## USER ROLES
Traveler (customer) · Support/Operator (staff) · Admin · Super Admin — database-driven RBAC, enforced server-side.

## TECH STACK (free/open-source first)
Backend: Python 3.12 + FastAPI + SQLAlchemy(async) + Alembic · Frontend: Next.js 16 + React 19 + TS + Tailwind v4 + Framer Motion · DB: PostgreSQL 16 · Cache/jobs: Redis + Celery · AI: Gemini (free) · OCR: Tesseract/EasyOCR/PaddleOCR (benchmark) · Travel: Amadeus Self-Service (free test) + mock fallback · Payments: Stripe test · Messaging: Meta WhatsApp + Klaviyo · DevOps: Docker + GitHub Actions.

## ARCHITECTURE (summary — see docs/ARCHITECTURE.md)
Modular monolith: Next.js → FastAPI (`/api/v1`) with modules {auth, users, admin, subscriptions, payments, travel, documents, ai/chatbot, ocr, notifications, locations, analytics, audit, config}; Redis + Celery workers; PostgreSQL; object/file storage for uploads. Boots without external services (health/readiness reports dependency status).

## DATABASE (see docs/DATABASE.md)
PostgreSQL only (no MongoDB). Entities planned: users, roles, permissions, role_permissions, user_roles, refresh_tokens, email_verifications, password_resets · plans, plan_features, subscriptions, payments, invoices, usage_counters · countries, cities, currencies, locales, visa_rules, app_config · trips, trip_searches, trip_items, itineraries · documents, document_files, document_analyses, extracted_fields · chat_conversations, chat_messages, ai_requests, ocr_jobs · notifications, whatsapp_messages, email_events · audit_logs, integration_logs. UUID PKs, timestamps mixin, PII encrypted, IDOR-safe ownership.

## AI (see docs — to be filled in P6/P7)
Chatbot: Gemini grounded on curated travel/visa KB + market config, intent detection, confidence + honest fallback. Documents: OCR → LLM field extraction → rule validation → corrections → compliance vs visa_rules. **Evaluation datasets + measured accuracy** recorded in AI_EVALUATION.md / OCR_EVALUATION.md (never claimed without measurement).

## INTEGRATIONS (status)
| Integration | Purpose | Env var(s) | Status |
|---|---|---|---|
| PostgreSQL | primary DB | POSTGRES_*/DATABASE_URL | wired (foundation) |
| Redis | cache/broker | REDIS_*/REDIS_URL | wired (foundation) |
| Gemini | chatbot + doc AI | GEMINI_API_KEY | pending (P6) |
| Amadeus | flights/hotels | AMADEUS_CLIENT_ID/SECRET | pending (P5) |
| Stripe | subscriptions | STRIPE_SECRET_KEY/WEBHOOK_SECRET | pending (P9) |
| Meta WhatsApp | messaging | WHATSAPP_* | pending (P8) |
| Klaviyo | email | KLAVIYO_API_KEY | pending (P8) |
| Google Maps | maps (optional) | GOOGLE_MAPS_API_KEY | optional |

## UI/UX (see docs/ARCHITECTURE.md + globals.css)
Design system from logo: deep navy (#16255C) + teal (#19B6C9) + cyan (#3DDCEB), AI accent violet (#7C5CFC). Tokens in `frontend/src/app/globals.css` (@theme). Framer Motion animations, `prefers-reduced-motion` respected. Brand centralised in `frontend/src/lib/brand.ts`. Logo SVGs in `frontend/public/brand/`.

## FRONTEND AUTH (Phase 4b)
Pages: /login, /register, /forgot-password, /reset-password, protected /dashboard (guarded by `src/app/dashboard/layout.tsx`). API client `src/lib/api.ts` (typed, parses error envelope). Auth state `src/lib/auth-context.tsx` (AuthProvider/useAuth): access token in memory, refresh token in localStorage, bootstrap via /refresh on mount, login/register/logout. UI primitives in `src/components/ui/` (Button, Input, Alert) + AuthShell. Navbar is auth-aware. Set NEXT_PUBLIC_API_BASE_URL for the backend. NOTE: refresh token in localStorage is an accepted FYP trade-off (httpOnly-cookie sessions = future hardening). Browser E2E couldn't run here (automation Chrome can't reach localhost) — verified via live backend HTTP smoke + build; run `docker compose up` or the two dev servers to view.

## SECURITY (see docs/SECURITY.md)
Argon2 hashing, JWT (access+refresh rotation), server-side RBAC, Pydantic validation, security headers + correlation IDs (middleware), strict CORS, Redis rate limiting (P4+), file-upload hardening, PII encryption + short retention/auto-delete, Stripe/WhatsApp webhook signature verification, secrets only in `.env`, audit logs, OWASP review per phase. Gitleaks in CI.

## TESTING & QA
Backend: pytest 19/19 passing — 5 foundation (health, headers, correlation id, OpenAPI) + 14 auth/RBAC (register, duplicate, weak-password, login success/failure, /me auth, refresh rotation + single-use reuse, logout revoke, email verify, password reset, non-enumerating reset request, rate limit 429, expired token, role + permission guards). Tests run on async SQLite (portable GUID type); production is PostgreSQL. Frontend: next build passing. E2E (Playwright), AI/OCR eval suites added in later phases. CI gates on every push/PR.

## AUTH DESIGN (Phase 4)
Argon2id password hashing (argon2-cffi) · JWT access token (HS256, 15 min, type-checked) · opaque refresh tokens (sha256-hashed in DB, rotated single-use, revocable, 7 days) · email-verification & password-reset tokens (sha256-hashed, expiring, single-use; reset revokes all refresh tokens) · RBAC via roles/permissions tables seeded from app/core/rbac.py (traveler/staff/admin/super_admin) · guards `require_roles` / `require_permissions` in app/api/deps.py (server-side) · in-memory auth rate limiter (Redis for prod). Endpoints under /api/v1/auth: register, login, refresh, logout, me, verify-email, password-reset/request, password-reset/confirm. Superuser bootstrap via env (SUPERUSER_EMAIL/PASSWORD) in app/db/init_db.py — no hardcoded creds. Known trade-offs: register returns 409 on existing email (mild enumeration, common UX); refresh reuse fails but no family-wide revocation yet.

## DEVELOPMENT PROGRESS (phase tracker)
```
Phase 0  Discovery & Analysis        [COMPLETE]  (approved by owner)
Phase 1  System Architecture         [IN PROGRESS] (docs/ARCHITECTURE.md, DATABASE.md written)
Phase 2  Design System & UI shell    [IN PROGRESS] (tokens + brand + landing page done)
Phase 3  Project Foundation          [COMPLETE]  (backend+frontend+docker+CI+docs; tests green)
Phase 4  Authentication & RBAC       [COMPLETE]  (register/login/refresh/logout/verify/reset, JWT+Argon2, RBAC guards, rate limit, migration; 19 tests)
Phase 5  Core travel features        [COMPLETE] backend (locations/visa, flight+hotel search mock+Amadeus, trips IDOR-safe, itinerary; 29 tests) + planner UI (/dashboard/plan, /trips, /trips/[id])
Phase 6  AI chatbot + evaluation     [BACKEND DONE] Gemini 2.5 Flash + intent/grounding + keyless fallback; eval 100%/100%; 36 tests. Chat UI = NEXT
Phase 7  OCR + document verification [PENDING]
Phase 8  External integrations       [PENDING]
Phase 9  Subscriptions + entitlements[PENDING]
Phase 10 Admin                       [PENDING]
Phase 11 Security hardening          [PENDING]
Phase 12 QA                          [PENDING]
Phase 13 Performance                 [PENDING]
Phase 14 CI/CD & deployment          [PENDING]
Phase 15 Final adversarial audit     [PENDING]
```

## IMPORTANT DECISIONS (log)
```
Decision: PostgreSQL only — drop MongoDB (proposal listed it).
Reason: Owner directive + reduce attack surface/ops; JSONB covers flexible doc/log storage.
Date: 2026-10-06

Decision: Amadeus Self-Service (free test) for flights/hotels + provider abstraction + mock fallback.
Reason: Booking.com/Expedia need commercial partnerships unavailable to an FYP; app must demo without live keys.
Date: 2026-10-06

Decision: Gemini (free tier) as the LLM; OCR engine chosen after benchmark.
Reason: Owner provides Gemini key; "use best free resources" directive.
Date: 2026-10-06

Decision: Dubai-first but fully configurable (DB-driven locations/visa rules).
Reason: Master prompt; future GCC/international expansion without rewrite.
Date: 2026-10-06

Decision: Modular monolith (not microservices) for v1.
Reason: Simplest architecture meeting scope; clean module boundaries allow later split.
Date: 2026-10-06
```

## RECOVERY NOTES
- Verify documented state against code before trusting this file.
- Backend runs without DB for health; DB features need PostgreSQL (via docker compose).
- First commit/push pending valid GitHub credentials for Mazharsial/JourneyJunction_FYP.
