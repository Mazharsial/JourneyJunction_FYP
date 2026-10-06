# Performance — Journey Junction

Measure first, optimise what matters. Current optimisations:

## Database
- **Async everywhere** (FastAPI + SQLAlchemy async + asyncpg) — no blocking I/O on the event loop;
  the synchronous Stripe SDK is run in a threadpool.
- **Indexes** on every foreign key and hot lookup column (email, iata_code, token hashes, user_id on
  owned resources, stripe ids, audit action) — see migrations.
- **No N+1:** relationships that are always rendered use `lazy="selectin"` (roles→permissions,
  trip→items, document→analysis→fields, conversation→messages), so a list loads in O(1) extra queries.
- **Bounded reads:** list endpoints (trips, documents, notifications, chat, audit, users) are limited
  / paginated — no unbounded table scans returned to clients.

## Caching
- **Reference data** (countries, cities, currencies, visa lookups, default market) and **plans** are
  read on nearly every page but change rarely → cached in-process with a TTL (`app/core/cache.py`),
  **invalidated on admin mutations** (visa-rule and plan-feature edits) and by TTL. This removes the
  repeated DB round-trips behind the trip planner and billing pages.
- Cached values are serialized Pydantic objects (session-independent), never ORM rows.
- **Upgrade path:** swap the in-process `TTLCache` for Redis (already a dependency) to share the
  cache across multiple workers in production.

## External calls
- Gemini / Amadeus / WhatsApp / Klaviyo / Stripe calls are isolated behind service clients with
  timeouts and graceful fallbacks, so a slow third party degrades one feature rather than the app.
- AI/OCR work is synchronous per request today; the Celery worker is wired for moving long OCR/AI
  jobs to the background if needed.

## Frontend
- Next.js production build: marketing + auth + dashboard pages are statically prerendered where
  possible; the trip-detail page is server-rendered on demand. Images use `next/image`; brand assets
  are lightweight SVGs. Tailwind purges unused CSS at build.

## Not prematurely optimised (deliberate)
- Rate limiting + cache are in-process (single-worker friendly); both have a documented Redis upgrade.
- No query-level micro-tuning until a real profiler/load test identifies a hotspot.
