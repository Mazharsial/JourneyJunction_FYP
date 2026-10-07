# PROJECT_CONTEXT.md — Journey Junction (single source of truth)

> This file is the project's living memory. Anyone (human or AI) should be able to read this +
> the repo + the proposal and continue development without the prior conversation.
> **Keep it updated after every meaningful task.** Never store real secrets here.

---

## CURRENT PROJECT STATE
```
Current Phase:      ALL core phases (0–15) COMPLETE. All 6 external integrations LIVE.
                    UI redesign + responsive pass done. Permanent Render+Vercel deploy = optional/next.
Current Feature:    Temporary live hosting via ngrok (production Next build + FastAPI); landing+dashboard
                    redesign (mega-menu, animated hero demo, left-sidebar dashboard, image cards).
Last Completed:     Mobile responsiveness fixes (grid-cols-1 base on all grids, min-w-0 on flex rows,
                    global overflow-x guard); assistant official-source links + dynamic follow-ups;
                    visa types + full chatbot grounding; Saudi + Umrah/Hajj; booking/verify links;
                    step-by-step preparation guide; admin panel buildout (plans/visa/health).
Last Successful Test: backend 95/95 pytest; frontend production build clean (16 routes).
Last Git Commit:    4243815 (mobile responsiveness). All pushed to origin/main.
Current Branch:     main
Live demo:          https://nonanarchically-rambunctious-lashay.ngrok-free.dev (temporary; tunnel to
                    local prod servers — only up while the dev machine + ngrok run).
Next Task:          (optional) Permanent deployment — Render (FastAPI + managed Postgres via render.yaml)
                    + Vercel (Next frontend). Create custom WhatsApp message templates (Meta approval).
Blocked By:         Nothing functional. Gemini free tier can hit 429 quota under heavy use (rich grounded
                    fallback covers it). WhatsApp dev token is temporary (24h) — regenerate / make permanent.
Supervisor doc:     docs/Journey_Junction_Project_Documentation.docx (updated; TOC: open in Word, press F9).
Credentials status: Gemini ✅ live · Stripe test ✅ live · Travelpayouts (flights) ✅ live ·
                    Geoapify (hotels) ✅ live · Klaviyo (email) ✅ live · WhatsApp (Meta) ✅ live (24h dev token).
                    All secrets in gitignored .env only.
Known Issues:       npm braces advisory (dev-only, no runtime impact). Gemini 429 under heavy use.
```

---

## PROJECT IDENTITY
- **Name:** Journey Junction (brand configurable via `BRAND_NAME` / `NEXT_PUBLIC_BRAND_NAME`; formerly "Tripzy"; may change).
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
Backend: Python 3.12 + FastAPI + SQLAlchemy(async) + Alembic · Frontend: Next.js 16 + React 19 + TS + Tailwind v4 + Framer Motion · DB: PostgreSQL 16 (dev uses SQLite via portable GUID type) · Cache/jobs: Redis + Celery · AI: Google Gemini 2.5 Flash (chat + vision OCR) · Flights: **Travelpayouts/Aviasales** (free, cached fares) + mock fallback · Hotels: **Geoapify Places** (free, real hotels; prices/ratings estimated) + mock fallback · Payments: Stripe test · Messaging: Meta WhatsApp Cloud API · Email/marketing: Klaviyo · DevOps: Docker + GitHub Actions.
NOTE: Amadeus Self-Service was the original flight/hotel plan but Amadeus **retired its free self-service tier (17 Jul 2026)**, so flights moved to Travelpayouts and hotels to Geoapify (Hotellook's free endpoint was also retired). The Amadeus provider remains in the codebase, unused.

## ARCHITECTURE (summary — see docs/ARCHITECTURE.md)
Modular monolith: Next.js → FastAPI (`/api/v1`) with modules {auth, users, admin, subscriptions, payments, travel, documents, ai/chatbot, ocr, notifications, locations, analytics, audit, config}; Redis + Celery workers; PostgreSQL; object/file storage for uploads. Boots without external services (health/readiness reports dependency status).

## DATABASE (see docs/DATABASE.md)
PostgreSQL only (no MongoDB). Entities planned: users, roles, permissions, role_permissions, user_roles, refresh_tokens, email_verifications, password_resets · plans, plan_features, subscriptions, payments, invoices, usage_counters · countries, cities, currencies, locales, visa_rules, app_config · trips, trip_searches, trip_items, itineraries · documents, document_files, document_analyses, extracted_fields · chat_conversations, chat_messages, ai_requests, ocr_jobs · notifications, whatsapp_messages, email_events · audit_logs, integration_logs. UUID PKs, timestamps mixin, PII encrypted, IDOR-safe ownership.

## AI (see docs — to be filled in P6/P7)
Chatbot: Gemini grounded on curated travel/visa KB + market config, intent detection, confidence + honest fallback. Documents: OCR → LLM field extraction → rule validation → corrections → compliance vs visa_rules. **Evaluation datasets + measured accuracy** recorded in AI_EVALUATION.md / OCR_EVALUATION.md (never claimed without measurement).

## INTEGRATIONS (status)
| Integration | Purpose | Env var(s) | Status |
|---|---|---|---|
| PostgreSQL / SQLite | primary DB (prod Postgres, dev SQLite) | POSTGRES_*/DATABASE_URL | ✅ live |
| Redis | cache/broker | REDIS_*/REDIS_URL | wired (foundation) |
| Gemini 2.5 Flash | chatbot + vision OCR | GEMINI_API_KEY | ✅ live (free tier; 429 under heavy use → rich grounded fallback) |
| Travelpayouts/Aviasales | flight fares (real cached) | TRAVELPAYOUTS_TOKEN / TRAVELPAYOUTS_MARKER | ✅ live (mock fallback for empty routes) |
| Geoapify Places | real hotels (prices estimated) | GEOAPIFY_API_KEY | ✅ live (mock fallback) |
| Stripe | subscriptions + entitlements | STRIPE_SECRET_KEY/WEBHOOK_SECRET | ✅ live (test mode) |
| Meta WhatsApp | notifications | WHATSAPP_ACCESS_TOKEN / _PHONE_NUMBER_ID / _VERIFY_TOKEN / _APP_SECRET | ✅ live (24h dev token; template fallback outside 24h window) |
| Klaviyo | email / marketing events | KLAVIYO_API_KEY | ✅ live (events drive Klaviyo Flows) |
| Amadeus Self-Service | flights/hotels (legacy) | AMADEUS_CLIENT_ID/SECRET | ❌ retired by Amadeus 17 Jul 2026; code kept, unused |
| Google Maps | maps (optional) | GOOGLE_MAPS_API_KEY | optional / unused |

Booking/verify deep links: flights → Aviasales (Travelpayouts marker), hotels → Booking.com search — shown on every offer.

## UI/UX (see docs/ARCHITECTURE.md + globals.css)
Design system from logo: deep navy (#16255C) + teal (#19B6C9) + cyan (#3DDCEB), AI accent violet (#7C5CFC). Tokens in `frontend/src/app/globals.css` (@theme). Framer Motion animations, `prefers-reduced-motion` respected. Brand centralised in `frontend/src/lib/brand.ts`. Logo SVGs in `frontend/public/brand/`.

## FRONTEND AUTH (Phase 4b)
Pages: /login, /register, /forgot-password, /reset-password, protected /dashboard (guarded by `src/app/dashboard/layout.tsx`). API client `src/lib/api.ts` (typed, parses error envelope). Auth state `src/lib/auth-context.tsx` (AuthProvider/useAuth): access token in memory, refresh token in localStorage, bootstrap via /refresh on mount, login/register/logout. UI primitives in `src/components/ui/` (Button, Input, Alert) + AuthShell. Navbar is auth-aware. Set NEXT_PUBLIC_API_BASE_URL for the backend. NOTE: refresh token in localStorage is an accepted FYP trade-off (httpOnly-cookie sessions = future hardening). Browser E2E couldn't run here (automation Chrome can't reach localhost) — verified via live backend HTTP smoke + build; run `docker compose up` or the two dev servers to view.

## SECURITY (see docs/SECURITY.md)
Argon2 hashing, JWT (access+refresh rotation), server-side RBAC, Pydantic validation, security headers + correlation IDs (middleware), strict CORS, Redis rate limiting (P4+), file-upload hardening, PII encryption + short retention/auto-delete, Stripe/WhatsApp webhook signature verification, secrets only in `.env`, audit logs, OWASP review per phase. Gitleaks in CI.

## TESTING & QA
Backend: **95/95 pytest passing** (auth/RBAC, travel+requirements+visa-types+pilgrimage, chat+grounding evals, documents+OCR evals, billing+entitlements, admin, notifications, full user-journey E2E, access-control matrix, adversarial audit). Tests run on async in-memory SQLite (portable GUID type); production is PostgreSQL. Frontend: production `next build` clean (16 routes, TypeScript + lint pass). Measured accuracy: chatbot intent/grounding evals and OCR field evals in AI_EVALUATION.md / OCR_EVALUATION.md. CI (GitHub Actions) gates on every push/PR: backend tests + frontend build + pip-audit + npm audit + gitleaks.

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
Phase 6  AI chatbot + evaluation     [COMPLETE] Gemini 2.5 Flash + grounding + keyless fallback + chat UI; eval 100%/100%
Phase 7  OCR + document verification [COMPLETE] hardened upload+encryption, Gemini Vision OCR+mock, validation, compliance + /dashboard/documents UI; evals 100%/100%; 46 tests
Phase 9  Subscriptions + entitlements[COMPLETE] plans/features seed, server-side usage limits (chat+OCR), Stripe checkout/portal/webhook, billing UI; 51 tests; live Stripe verified
Phase 10 Admin panel                 [COMPLETE] perm-gated admin: users/roles/plans/visa/stats/audit/health + UI; audit logging; 59 tests
Phase 8  WhatsApp + Klaviyo          [COMPLETE] WhatsApp Cloud API + Klaviyo (abstraction) + mock fallback, notification_service wired to events, prefs + webhook + settings UI; 65 tests. Live when keys added.
Phase 11 Security hardening          [COMPLETE] all backend deps patched (pip-audit clean), OWASP self-review, CI dep scans; dev-only braces advisory accepted (no fix, not in runtime)
Phase 12 QA                          [COMPLETE] 91 tests; full journey E2E + access-control matrix; TESTING.md
Phase 13 Performance                 [COMPLETE] in-process TTL cache (locations/plans) + admin invalidation; selectin/indexes/async; PERFORMANCE.md
Phase 15 Final adversarial audit     [COMPLETE] audit tests (IDOR/escalation/disabled-token/leakage/webhook) + production SECRET_KEY boot guard
Phase 14 CI/CD & Deployment          [CI DONE; TEMP-LIVE] GitHub Actions CI green; app temporarily live via
                                     ngrok (prod Next build + FastAPI). Permanent Render+Vercel = optional next.

POST-PLAN ENHANCEMENTS (after the 8-week plan; all COMPLETE + pushed)
- Integrations taken LIVE: Travelpayouts (flights), Geoapify (hotels), Gemini, Stripe, Klaviyo, WhatsApp.
- Markets: restricted to Pakistan (home) + UAE + Saudi Arabia; added Umrah & Hajj trip purposes.
- Travel requirements feature: visa types (researched 2026), required-document compliance check vs the
  user's verified documents, health/currency/customs/emergency info, and a step-by-step preparation guide
  (passport → attestation → visa → vaccinations → booking) with fees, timelines and official-source links.
- Booking/verify deep links on every flight (Aviasales) and hotel (Booking.com).
- AI assistant: official-source links + dynamic, context-aware follow-up suggestions; full knowledge-base
  grounding (visa types/docs/health); rich grounded fallback when Gemini is rate-limited.
- Admin panel buildout: plan-entitlement editor, visa-rule CRUD, real integration health, verify toggle.
- UI redesign: mega-menu navbar, two-column hero with an auto-cycling animated product demo, left-sidebar
  dashboard (no duplicated nav), image cards with hover animations; full mobile-responsiveness pass.
- Serving: production Next build (stable chunks) behind the ngrok tunnel; `output:"standalone"` gated on
  NEXT_STANDALONE so local `next start` keeps the /api/* proxy working.
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

Decision: Replace Amadeus with Travelpayouts (flights) + Geoapify (hotels).
Reason: Amadeus retired its free self-service tier (17 Jul 2026); Hotellook's free endpoint also gone.
        Travelpayouts gives real cached fares (free); Geoapify gives real hotels (prices estimated). Mock stays as fallback.
Date: 2026-10-07

Decision: Restrict markets to Pakistan + UAE + Saudi Arabia; add Umrah/Hajj trip purposes.
Reason: Owner directive (home market Pakistan; UAE + Saudi are the relevant destinations incl. pilgrimage).
Date: 2026-10-06/07

Decision: Serve the live demo from a production Next build (not the dev server) behind ngrok.
Reason: Turbopack dev chunk-drift over the tunnel broke hydration; prod build is stable. output:"standalone"
        gated behind NEXT_STANDALONE so local `next start` still applies the /api/* rewrite proxy.
Date: 2026-10-07

Decision: WhatsApp notifications fall back to an approved template outside the 24h customer-service window.
Reason: Meta only allows free-form text within 24h of a user message; business-initiated sends need templates.
        Custom templates (real text) require Meta approval — swap in once approved.
Date: 2026-10-07
```

## RECOVERY NOTES
- Verify documented state against code before trusting this file.
- Backend runs without DB for health; DB features need PostgreSQL (via docker compose).
- First commit/push pending valid GitHub credentials for Mazharsial/JourneyJunction_FYP.
