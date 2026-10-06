# Security — VoynixAI

Security is a cross-cutting concern reviewed at every phase (OWASP Top-10 based). This document
grows as controls are implemented; the foundation items below are already in place.

## Implemented (foundation)
- **Security headers** middleware: `X-Content-Type-Options`, `X-Frame-Options: DENY`,
  `Referrer-Policy`, `Permissions-Policy`, strict `Content-Security-Policy` on the JSON API
  (relaxed only for `/docs`), HSTS in production.
- **Correlation IDs** per request, bound to structured logs, echoed as `X-Request-ID`.
- **Safe error envelope**: no stack traces / SQL / paths / secrets returned to clients.
- **Secrets hygiene**: all secrets via `.env` only; `.env` git-ignored; `.env.example` committed;
  Gitleaks secret-scan in CI.
- **CORS**: restricted to configured origins.
- App **boots without external services**; dependency health via `/api/v1/health/ready`.

## Implemented (Phase 4 — authentication & RBAC)
- **Argon2id** password hashing (argon2-cffi) with opportunistic rehash.
- **JWT access tokens** (HS256, short-lived, type-checked) + **opaque refresh tokens** stored only as SHA-256 hashes, **rotated single-use** and revocable; logout and password-reset revoke them.
- **Email verification & password reset** via SHA-256-hashed, expiring, single-use tokens.
- **Server-side RBAC**: database-driven roles/permissions with `require_roles` / `require_permissions` guards.
- **Rate limiting** on auth endpoints (in-memory now; Redis for production).
- **Non-enumerating** password-reset request; generic login failure message.
- All verified by 14 auth/RBAC integration tests.

## Implemented (Phase 7 — document uploads, sensitive PII)
- **Upload hardening**: size limit, extension allow-list, declared-MIME allow-list, and **magic-byte
  content sniffing** (rejects a spoofed Content-Type). Stored filename is a UUID — the user's
  filename never touches disk, so path traversal is impossible.
- **Encryption at rest**: files encrypted with Fernet (AES-128-CBC + HMAC) keyed from SECRET_KEY,
  stored outside the web root, **never served statically**; plaintext only transiently in memory.
- **Consent required** before processing; **short retention** (`retention_until`, default 30 days).
- **IDOR-safe** ownership on every document/analysis read + delete.
- Rate-limited upload + AI-vision endpoints.

## Implemented (Phase 9 — billing)
- **Server-side entitlement enforcement**: AI messages and OCR documents are gated by the user's
  plan and monthly usage **in the backend** (402/403), not just hidden in the UI — a direct API
  call by a free user past their limit is rejected.
- **Stripe webhook signature verification** (`stripe.Webhook.construct_event` + `STRIPE_WEBHOOK_SECRET`);
  unsigned/invalid events are rejected (400).
- Secret key never exposed to the frontend (only the publishable key is).

## Phase 11 — Security hardening & dependency audit
**Dependency vulnerability scan** (now run in CI on every push):
- **Backend (`pip-audit`):** found CVEs in `pillow`, `pyjwt`, `cryptography`, `python-multipart`,
  `starlette`, `pytest`. **Fixed** by upgrading (fastapi 0.115→0.142, starlette 0.41→1.7, pyjwt
  2.10→2.15, cryptography 44→50, Pillow 11.1→12.3, python-multipart 0.0.20→0.0.31, pytest 8→9).
  → **`pip-audit`: no known vulnerabilities.** All 65 tests still pass after the upgrade.
- **Frontend (`npm audit`):** 5 high advisories, all in one **dev-only** chain
  (`braces`→`micromatch`→`fast-glob`→`@next/eslint-plugin-next`→`eslint-config-next`). `micromatch`
  and `braces` forced to latest via `overrides`. The remaining `braces` advisory (stack-exhaustion
  DoS, range `<=3.0.3`) has **no published fix** and is **dev-tooling only** — it runs the linter on
  our own source paths at build time, is never in the shipped runtime bundle, and is not
  attacker-reachable in production. **Accepted risk**; CI audits production deps (`--omit=dev`).

**OWASP review (self-audit):** SQLi (ORM/parameterized ✓), XSS (output-encoded + CSP ✓), authn/z
(Argon2 + JWT + server-side RBAC ✓), IDOR (ownership checks across trips/documents/chat/subscriptions
✓), broken access control (entitlements enforced server-side ✓), security misconfig (headers + CORS +
no secrets committed + gitleaks ✓), sensitive data (PII encryption + retention ✓), SSRF (only
first-party outbound to Gemini/Stripe/Meta/Klaviyo ✓), components with known vulns (fixed above ✓),
upload abuse (type/MIME/magic/size + UUID names ✓), rate-limit abuse (auth/AI/upload limited ✓).

## Planned (by phase)
| Control | Phase |
|---|---|
| Scheduled retention cleanup job (Celery beat) for expired documents | later |
| Redis-based distributed rate limiting + X-Forwarded-For handling | later |
| Refresh-token reuse detection (family revocation) | later |
| Optional anti-virus scan on uploads | later |
| PII encryption at rest + retention/auto-delete for documents | P7 |
| Stripe + WhatsApp webhook signature verification | P8/P9 |
| Subscription entitlement enforcement (no frontend-only gating) | P9 |
| Dependency audit (pip-audit / npm audit) + fixes | P11 |
| Full OWASP audit + penetration pass | P11/P15 |

## Threats explicitly addressed
SQLi (parameterised ORM), XSS (output encoding + CSP), CSRF (where cookie-based), SSRF (allow-listed
outbound calls), IDOR/mass-assignment (ownership checks + explicit schemas), broken auth/z, upload
abuse, rate-limit abuse, secret/credential leakage, session attacks.

## Data privacy
Passport/visa documents are sensitive PII (GDPR / UAE PDPL aware): explicit consent, encryption,
minimal + time-boxed retention, auto-deletion, strict access control. Travel/visa guidance is
**informational only**, not legal advice (disclaimed in the UI).
