# Roadmap — VoynixAI

Each phase ends with: tests + QA + security check → update `PROJECT_CONTEXT.md` → commit → push.

| Phase | Deliverable | Status |
|---|---|---|
| 0 | Discovery & analysis (requirements, roles, journeys, architecture) | ✅ Complete |
| 1 | System architecture + DB/API/AI/security design docs | 🟡 In progress |
| 2 | Design system + UI shell (tokens, brand, landing) | 🟡 In progress |
| 3 | Foundation (repo, FastAPI+Next scaffold, DB, Docker, logging, CI) | ✅ Complete |
| 4 | Authentication & RBAC (register/login/verify/reset, roles, JWT) | ✅ Complete |
| 5 | Core travel (flights/hotels/itinerary via Amadeus + mock; locations/visa config) | ✅ Complete (backend + planner UI) |
| 6 | AI chatbot + evaluation (≥90% measured) | ✅ Complete (backend + chat UI; 100%/100% measured) |
| 7 | OCR + document verification/correction + evaluation (≥90% measured) | 🟡 Backend done (validation 100%, OCR 100% measured); upload UI next |
| 8 | Integrations (Stripe → WhatsApp → Klaviyo) | ⬜ |
| 9 | Subscriptions + enforced entitlements + usage limits | ⬜ |
| 10 | Admin panel | ⬜ |
| 11 | Security hardening (OWASP, dependency audit) | ⬜ |
| 12 | QA (unit/integration/E2E/regression) | ⬜ |
| 13 | Performance (profiling, caching, optimisation) | ⬜ |
| 14 | CI/CD & deployment (free hosting) | ⬜ |
| 15 | Final adversarial audit | ⬜ |

## MVP priority (given 8-week proposal window)
P0 for a demoable MVP: **auth → core travel (with mock fallback) → AI chatbot → OCR document
verification → subscriptions**. Admin, WhatsApp/Klaviyo, performance and deployment follow.
