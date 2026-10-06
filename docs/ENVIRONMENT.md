# Environment & Configuration — Journey Junction

All configuration is environment-driven. Copy `.env.example` → `.env` (root, used by docker-compose
and the backend) and `frontend/.env.example` → `frontend/.env.local`. **Never commit real values.**

## How settings load
- **Backend:** `app/core/config.py` (`pydantic-settings`) reads env / `.env`. Access via
  `get_settings()`. `DATABASE_URL` and `REDIS_URL` are derived from parts if not set explicitly.
- **Frontend:** `NEXT_PUBLIC_*` values are read in `src/lib/brand.ts` (exposed to the browser —
  never put secrets in `NEXT_PUBLIC_*`).

## Variables
| Variable | Used by | Phase | Notes |
|---|---|---|---|
| `BRAND_NAME` | backend | now | Brand label (default Journey Junction) |
| `SECRET_KEY` | backend | now | JWT/signing. Generate: `python -c "import secrets;print(secrets.token_urlsafe(48))"` |
| `POSTGRES_*` / `DATABASE_URL` | backend | now | PostgreSQL connection |
| `REDIS_*` / `REDIS_URL` | backend/worker | now | Cache + Celery broker |
| `CORS_ORIGINS` | backend | now | Comma-separated allowed origins |
| `DEFAULT_COUNTRY/CITY/CURRENCY/LOCALE/TIMEZONE` | backend | now | Seeded market (Dubai) |
| `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS` | backend | P4 | Auth token lifetimes |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | backend | P6 | AI chatbot + document analysis |
| `AMADEUS_CLIENT_ID/SECRET`, `AMADEUS_ENV` | backend | P5 | Flights/hotels (free test env) |
| `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PUBLISHABLE_KEY` | backend/frontend | P9 | Subscriptions (test mode) |
| `WHATSAPP_ACCESS_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_VERIFY_TOKEN`, `WHATSAPP_APP_SECRET` | backend | P8 | Meta WhatsApp Cloud API |
| `KLAVIYO_API_KEY` | backend | P8 | Email |
| `GOOGLE_MAPS_API_KEY` | frontend/backend | optional | Maps |
| `NEXT_PUBLIC_API_BASE_URL` | frontend | now | Backend API base |

## Getting the free credentials (when each phase needs them)
- **Gemini:** Google AI Studio → API key (free tier).
- **Amadeus:** developers.amadeus.com → Self-Service app → test API key/secret (free).
- **Stripe:** dashboard.stripe.com (test mode) → `STRIPE_SECRET_KEY` + `STRIPE_PUBLISHABLE_KEY`.
  - Products/prices are created automatically on first `init_db` run (idempotent via `lookup_key`).
  - **Webhooks (to auto-update plans after checkout):** run `stripe listen --forward-to localhost:8000/api/v1/billing/webhook`; it prints a `whsec_…` signing secret → put it in `STRIPE_WEBHOOK_SECRET`.
  - **Test card:** `4242 4242 4242 4242`, any future expiry, any CVC/ZIP.
- **Meta WhatsApp:** developers.facebook.com → your app → WhatsApp → Step 1 → **Generate token** (`WHATSAPP_ACCESS_TOKEN`, ~24h temp) + copy **Phone Number ID** (`WHATSAPP_PHONE_NUMBER_ID`); add your own number as a verified test recipient. Outbound messages work with just these. For inbound (webhook) also set `WHATSAPP_VERIFY_TOKEN` (any string) + `WHATSAPP_APP_SECRET` (App settings → Basic) and expose `/api/v1/notifications/whatsapp/webhook` publicly (e.g. ngrok).
- **Klaviyo:** Klaviyo account → Settings → API Keys → **Private API Key** (`KLAVIYO_API_KEY`). We upsert profiles + track events; configure Klaviyo **Flows** to turn events (welcome, trip_created, document_verified) into emails.

> Both WhatsApp and Klaviyo run in **mock mode** (notifications recorded but not sent) until the keys are set — the app and tests work without them.

The app runs in **mock/degraded mode** when an integration key is absent, so development is never blocked.
