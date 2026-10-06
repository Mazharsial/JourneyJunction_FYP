# Deployment — VoynixAI (Render + Vercel, free tier)

Backend API + PostgreSQL on **Render**, frontend on **Vercel**. Both have free tiers. Secrets are
set in each dashboard — never committed.

## A. Backend + database → Render
1. Push to GitHub (done). Go to **render.com → New → Blueprint** and connect `JourneyJunction_FYP`.
   Render reads `render.yaml` and creates **`voynixai-api`** (web service) + **`voynixai-db`** (Postgres).
2. On first deploy, set the `sync: false` env vars in the Render dashboard:
   - `CORS_ORIGINS` = your Vercel URL (set after step B; you can redeploy to add it).
   - `BILLING_SUCCESS_URL` / `BILLING_CANCEL_URL` = `https://<vercel-url>/dashboard/billing?status=success|cancel`
   - `SUPERUSER_EMAIL` / `SUPERUSER_PASSWORD` = your admin login (created on first boot).
   - Optional keys (`GEMINI_API_KEY`, `STRIPE_*`, `AMADEUS_*`, `WHATSAPP_*`, `KLAVIYO_API_KEY`) — add
     when ready; the app runs in mock mode without them.
   - `SECRET_KEY` and `DATABASE_URL` are set automatically.
3. The start command runs migrations + seeds (RBAC, locations, plans, Stripe catalog if configured)
   then launches uvicorn. Health check: `/api/v1/health`.
4. Note the service URL, e.g. `https://voynixai-api.onrender.com`.

> Free tier note: the web service sleeps after inactivity (first request wakes it, ~30s). Free
> Postgres has a limited lifetime — fine for an FYP demo.

## B. Frontend → Vercel
1. Go to **vercel.com → Add New → Project**, import the repo, and set **Root Directory = `frontend`**
   (Vercel auto-detects Next.js).
2. Add environment variable:
   - `NEXT_PUBLIC_API_BASE_URL` = `https://voynixai-api.onrender.com/api/v1`
3. Deploy. Note the URL, e.g. `https://voynixai.vercel.app`.
4. Back in Render, set `CORS_ORIGINS` (and the billing URLs) to this Vercel URL and redeploy.

## C. Stripe webhook (for live plan updates after checkout)
In the Stripe dashboard → Developers → Webhooks → add endpoint
`https://voynixai-api.onrender.com/api/v1/billing/webhook` (events: `checkout.session.completed`,
`customer.subscription.*`, `invoice.*`) → copy the signing secret into Render's `STRIPE_WEBHOOK_SECRET`.

## D. WhatsApp inbound webhook (optional)
Callback URL `https://voynixai-api.onrender.com/api/v1/notifications/whatsapp/webhook`, verify token =
`WHATSAPP_VERIFY_TOKEN`; also set `WHATSAPP_APP_SECRET`.

## Verify
- `https://voynixai-api.onrender.com/docs` (API docs) and `/api/v1/health` → `ok`.
- Open the Vercel URL → register → dashboard → plan a trip / chat / verify a document.
- Log in as the superuser → the **Admin** link appears.

## CI/CD
GitHub Actions (`.github/workflows/ci.yml`) runs tests, build, dependency audits and secret scanning
on every push. Render and Vercel auto-deploy on push to `main`.
