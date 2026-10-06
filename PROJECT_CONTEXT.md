# PROJECT_CONTEXT.md — VoynixAI (single source of truth)

> This file is the project's living memory. Anyone (human or AI) should be able to read this +
> the repo + the proposal and continue development without the prior conversation.
> **Keep it updated after every meaningful task.** Never store real secrets here.

---

## CURRENT PROJECT STATE
```
Current Phase:      Phase 3 — Foundation (COMPLETE); Phase 1/2 partially done (docs + design tokens)
Current Feature:    Project scaffold (backend + frontend + devops + docs)
Last Completed:     Foundation (backend tests green, frontend build green) + supervisor documentation (.docx)
Last Successful Test: backend `pytest` 5/5 passed; frontend `npm run build` succeeded
Last Git Commit:    fe2e408 — PUSHED to origin/main ✅
Current Branch:     main (develop to be created)
Next Task:          Phase 4 — Authentication & RBAC (users/roles/permissions, register/login/JWT)
Blocked By:         Nothing. CI enabled at .github/workflows/ci.yml (token now has `workflow` scope). Docker Desktop not installed locally (only needed to run full stack).
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

## SECURITY (see docs/SECURITY.md)
Argon2 hashing, JWT (access+refresh rotation), server-side RBAC, Pydantic validation, security headers + correlation IDs (middleware), strict CORS, Redis rate limiting (P4+), file-upload hardening, PII encryption + short retention/auto-delete, Stripe/WhatsApp webhook signature verification, secrets only in `.env`, audit logs, OWASP review per phase. Gitleaks in CI.

## TESTING & QA
Backend: pytest (5/5 foundation tests passing — health, security headers, correlation id, OpenAPI). Frontend: next build (passing) + eslint. E2E (Playwright), AI/OCR eval suites, security tests added in later phases. CI gates on every push/PR (backend tests, frontend build, secret scan).

## DEVELOPMENT PROGRESS (phase tracker)
```
Phase 0  Discovery & Analysis        [COMPLETE]  (approved by owner)
Phase 1  System Architecture         [IN PROGRESS] (docs/ARCHITECTURE.md, DATABASE.md written)
Phase 2  Design System & UI shell    [IN PROGRESS] (tokens + brand + landing page done)
Phase 3  Project Foundation          [COMPLETE]  (backend+frontend+docker+CI+docs; tests green)
Phase 4  Authentication & RBAC       [PENDING]   <-- NEXT
Phase 5  Core travel features        [PENDING]
Phase 6  AI chatbot + evaluation     [PENDING]
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
