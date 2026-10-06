# Testing & QA — Journey Junction

## How to run
```bash
cd backend && pytest                 # all backend tests
cd backend && pytest -q tests/test_journey.py        # full user-journey E2E
cd frontend && npm run build         # type-check + build (CI gate)
```
CI runs backend tests, the frontend build, dependency audits and secret scanning on every push.

## Strategy (testing pyramid)
- **Unit / service:** entitlement limits, validation rules, intent detection, grounding, OCR
  evaluation — deterministic, offline.
- **Integration (API):** every module via httpx `AsyncClient` over the ASGI app against a fresh
  in-memory SQLite DB per test (portable `GUID` type; production is PostgreSQL). External services
  (Gemini, Stripe, WhatsApp, Klaviyo) are forced to **mock mode** in `conftest.py`, so the suite is
  fully offline and reproducible.
- **End-to-end journey:** `test_journey.py` chains register → preferences → plan trip → AI chat →
  document verification → notifications → usage tracking.
- **Access-control matrix:** `test_access_matrix.py` asserts every protected endpoint returns **401**
  anonymously and admin endpoints return **403** for non-admins; public endpoints stay open.
- **Measured AI accuracy (CI-gated ≥90%):** chatbot intent + grounding, document validation.

## Current results (87 backend tests passing)
| Area | What's covered |
|---|---|
| Auth & RBAC | register/login/refresh-rotation/logout/verify/reset, role & permission guards, expiry, rate limit |
| Travel | locations, visa lookup, flight/hotel search, trips (create/list/detail), IDOR, date validation |
| AI chatbot | grounded answers, history, out-of-scope, IDOR; **intent 100%, grounding 100%** |
| Documents | upload security (type/MIME/magic/size), encryption round-trip, analysis, IDOR, delete; **validation 100%** |
| Billing | plans, default free, Stripe-unconfigured paths, **server-side limit enforcement** (402) |
| Admin | access control, user management, self-deactivate block, super-admin restriction, visa CRUD, plan edits, audit |
| Notifications | welcome/trip/document events, preferences, test-send, WhatsApp webhook |
| Journey + matrix | full happy path + every protected endpoint's auth/role check |

## Live verifications (performed during development, documented in their phase docs)
- Gemini chatbot (grounded visa answer), Gemini Vision OCR (24/24 fields), Stripe (products + checkout
  session), travel planner over real HTTP.

## Known non-blocking items
- Deprecation warnings (Starlette `TestClient`/httpx, `HTTP_422` constant rename) — cosmetic.
- One dev-only npm advisory (`braces`, no published fix, not in runtime) — accepted (see SECURITY.md).
