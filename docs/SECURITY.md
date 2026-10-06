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

## Planned (by phase)
| Control | Phase |
|---|---|
| Argon2 password hashing | P4 |
| JWT access + refresh-token rotation, revocation | P4 |
| Server-side RBAC (roles/permissions) + IDOR ownership checks | P4+ |
| Redis-based rate limiting (auth, AI, uploads) | P4 |
| Email verification + secure password reset (hashed, expiring tokens) | P4 |
| File-upload hardening (type/MIME/size/ext/filename sanitisation, stored outside webroot, signed access) | P7 |
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
