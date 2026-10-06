# Database — Journey Junction (PostgreSQL only)

No MongoDB. Flexible/semi-structured data (AI payloads, logs, extracted fields) uses PostgreSQL
`JSONB`. UUID primary keys, timezone-aware `created_at`/`updated_at` (see `app/db/base.py` mixins),
explicit FKs, indexes and constraints. Migrations via Alembic (`backend/migrations`).

## Planned entities (built per phase)

### Identity & access (Phase 4)
- `users` (id, email unique, password_hash [argon2], full_name, is_active, is_verified, timestamps)
- `roles` (name, description) · `permissions` (code, description)
- `role_permissions` (role↔permission) · `user_roles` (user↔role)
- `refresh_tokens` (user_id, token_hash, expires_at, revoked_at)
- `email_verifications`, `password_resets` (user_id, token_hash, expires_at, used_at)

### Locations & configuration (Phase 5)
- `countries` (iso2, name, currency, is_active) · `cities` (country_id, name, timezone)
- `currencies` (code, symbol) · `locales` (code)
- `visa_rules` (origin_country, destination_country, requirements JSONB, source, updated_at)
- `app_config` (key, value JSONB) — runtime-tunable settings

### Travel (Phase 5)
- `trips` (user_id, destination_city_id, start_date, end_date, budget_tier, status)
- `trip_searches` (trip_id, params JSONB, provider, results_cached JSONB, created_at)
- `trip_items` (trip_id, type [flight|hotel], provider_ref, data JSONB, price, currency)
- `itineraries` (trip_id, day, items JSONB, generated_by)

### Documents & AI (Phases 6–7)
- `documents` (user_id, type [passport|visa|ticket|other], status, consent_at, retention_until)
- `document_files` (document_id, storage_path, mime, size, sha256) — encrypted at rest
- `document_analyses` (document_id, ocr_engine, confidence, findings JSONB, created_at)
- `extracted_fields` (analysis_id, field_name, raw_value, normalized_value, issue, suggestion)
- `ocr_jobs` (document_id, status, started_at, finished_at, error)
- `chat_conversations` (user_id, title) · `chat_messages` (conversation_id, role, content, meta JSONB)
- `ai_requests` (user_id, kind, tokens, latency_ms, model, status) — usage + cost tracking

### Billing (Phase 9)
- `plans` (code, name, price, currency, interval, stripe_price_id)
- `plan_features` (plan_id, feature_key, enabled, limit_value) — **entitlement source of truth**
- `subscriptions` (user_id, plan_id, stripe_subscription_id, status, current_period_end)
- `payments` (subscription_id, stripe_payment_intent, amount, currency, status)
- `invoices` (subscription_id, stripe_invoice_id, amount, pdf_url)
- `usage_counters` (user_id, feature_key, period_start, count) — enforced server-side

### Communication (Phase 8)
- `notifications` (user_id, channel, template, payload JSONB, status)
- `whatsapp_messages` (user_id, wa_message_id, direction, body, status)
- `email_events` (user_id, provider, event, payload JSONB)

### Observability (cross-cutting)
- `audit_logs` (actor_user_id, action, entity, entity_id, metadata JSONB, ip, created_at)
- `integration_logs` (service, request_id, status, latency_ms, error)

## Data protection
Passport/visa images are sensitive PII: stored encrypted, access-controlled by ownership (IDOR-safe),
with a `retention_until` and automatic deletion job. Minimal retention; raw images not kept long-term.
