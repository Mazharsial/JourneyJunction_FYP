# Architecture — VoynixAI

## Style
Modular **monolith** (single deployable FastAPI backend + Next.js frontend) with clean module
boundaries that can later be split into services. Chosen for simplicity at FYP scope without
sacrificing maintainability.

## High-level
```
┌────────────┐     HTTPS/JSON      ┌──────────────────────────────────────────┐
│ Next.js 16 │ ──────────────────▶ │ FastAPI  (/api/v1)                        │
│ (React 19) │ ◀────────────────── │  middleware: CORS · security headers ·    │
└────────────┘                     │              correlation-id · rate-limit  │
                                   │  auth/RBAC → business modules → services  │
                                   └───────┬───────────────┬──────────────┬────┘
                                           │               │              │
                                     SQLAlchemy        Celery tasks   integration
                                           │           (via Redis)    clients (HTTP)
                                   ┌───────▼─────┐   ┌─────▼─────┐  ┌────▼───────────────┐
                                   │ PostgreSQL  │   │  Redis    │  │ Gemini · Amadeus · │
                                   └─────────────┘   └───────────┘  │ Stripe · WhatsApp ·│
                                   file/object storage (uploads)    │ Klaviyo            │
                                                                     └────────────────────┘
```

## Backend modules (`backend/app`)
```
core/        config (env-driven), logging, middleware, exceptions, security (P4)
db/          async engine/session, declarative base + mixins
models/      ORM models (added per phase)
api/v1/      routers (health now; auth/trips/documents/... per phase)
worker/      Celery app + tasks
services/    business + integration logic (added per phase)
```

### Request lifecycle
1. CORS → SecurityHeaders → CorrelationId middleware (binds `request_id` to logs).
2. Route handler (Pydantic-validated) → auth/RBAC dependency → service layer → DB.
3. Errors pass through global handlers → consistent JSON envelope (no internals leaked).
4. Long/external work (OCR, AI, webhooks) is dispatched to Celery.

## Frontend (`frontend/src`)
```
app/         App Router pages (landing now; auth/dashboard/admin per phase)
components/  reusable UI (Navbar, Hero, Features, Footer, ...)
lib/         brand config, API client (per phase)
```
Tailwind v4 CSS-first tokens in `app/globals.css`; brand centralised in `lib/brand.ts`.

## Configurability (no hardcoding)
Brand, market (country/city/currency/locale/timezone), limits, pricing, feature entitlements and
visa rules are **env- or DB-driven**. Dubai is seeded as the first market, not hardcoded.

## Deployment
Local: `docker compose up` (postgres, redis, backend, worker, frontend). CI: GitHub Actions
(backend tests, frontend build, secret scan). Target free hosting later (e.g. Render/Railway free
tier for API+DB, Vercel for frontend) — evaluated in Phase 14.
