"use client";

import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { useAuth } from "@/lib/auth-context";
import { adminApi, type AdminPlan } from "@/lib/admin-api";

const FEATURE_LABELS: Record<string, string> = {
  chatbot_messages: "AI chatbot messages / month",
  ocr_documents: "Document verifications / month",
  trips: "Saved trips",
  whatsapp_alerts: "WhatsApp alerts",
};

function label(key: string) {
  return FEATURE_LABELS[key] ?? key.replace(/_/g, " ");
}

function price(cents: number, currency: string) {
  if (cents === 0) return "Free";
  return `${currency === "USD" ? "$" : currency + " "}${(cents / 100).toFixed(0)}`;
}

export function PlansManager() {
  const { authCall } = useAuth();
  const [plans, setPlans] = useState<AdminPlan[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [savingKey, setSavingKey] = useState<string | null>(null);
  // Local edits: `${code}:${feature}` -> { enabled, limit }
  const [edits, setEdits] = useState<Record<string, { enabled: boolean; limit: string }>>({});

  const load = useCallback(async () => {
    try {
      const rows = await authCall((t) => adminApi.plans(t));
      setPlans(rows);
      const init: Record<string, { enabled: boolean; limit: string }> = {};
      for (const p of rows)
        for (const f of p.features)
          init[`${p.code}:${f.feature_key}`] = {
            enabled: f.enabled,
            // -1 = unlimited -> shown as blank
            limit: f.limit_value === -1 || f.limit_value == null ? "" : String(f.limit_value),
          };
      setEdits(init);
    } catch {
      setError("Could not load plans.");
    }
  }, [authCall]);

  useEffect(() => {
    void load();
  }, [load]);

  async function save(code: string, feature: string) {
    const key = `${code}:${feature}`;
    const e = edits[key];
    if (!e) return;
    setSavingKey(key);
    setError(null);
    try {
      const limitTrim = e.limit.trim();
      // blank -> -1 (unlimited); otherwise the monthly cap (0 = disabled)
      const limit_value = limitTrim === "" ? -1 : Math.max(0, parseInt(limitTrim, 10) || 0);
      const updated = await authCall((t) =>
        adminApi.updatePlanFeature(t, code, { feature_key: feature, enabled: e.enabled, limit_value }),
      );
      setPlans((prev) => prev?.map((p) => (p.code === code ? updated : p)) ?? prev);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed.");
    } finally {
      setSavingKey(null);
    }
  }

  if (!plans) return <p className="text-sm text-muted">Loading plans…</p>;

  return (
    <section>
      <h2 className="text-lg font-semibold text-foreground">Plans &amp; entitlements</h2>
      <p className="mt-1 text-xs text-muted">
        Monthly limits are enforced server-side. Blank = unlimited · 0 = disabled · N = cap / month.
      </p>
      {error && <div className="mt-3"><Alert tone="error">{error}</Alert></div>}
      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
        {plans.map((p) => (
          <div key={p.code} className="rounded-2xl border border-border bg-surface p-5">
            <div className="flex items-baseline justify-between">
              <h3 className="font-bold text-foreground">{p.name}</h3>
              <span className="text-sm font-semibold text-brand-blue">
                {price(p.price_cents, p.currency)}
                {p.price_cents > 0 && <span className="text-xs font-normal text-muted">/{p.interval}</span>}
              </span>
            </div>
            <div className="mt-4 space-y-3">
              {p.features.length === 0 && <p className="text-xs text-muted">No features.</p>}
              {p.features.map((f) => {
                const key = `${p.code}:${f.feature_key}`;
                const e = edits[key] ?? { enabled: f.enabled, limit: "" };
                return (
                  <div key={f.feature_key} className="rounded-lg border border-border p-3">
                    <p className="text-sm font-medium text-foreground">{label(f.feature_key)}</p>
                    <div className="mt-2 flex items-center gap-3">
                      <label className="flex items-center gap-1.5 text-xs text-muted">
                        <input
                          type="checkbox"
                          checked={e.enabled}
                          onChange={(ev) => setEdits((s) => ({ ...s, [key]: { ...e, enabled: ev.target.checked } }))}
                        />
                        Enabled
                      </label>
                      <input
                        type="number"
                        min={0}
                        value={e.limit}
                        placeholder="∞"
                        onChange={(ev) => setEdits((s) => ({ ...s, [key]: { ...e, limit: ev.target.value } }))}
                        className="w-20 rounded-lg border border-border bg-surface px-2 py-1 text-sm outline-none focus:border-teal"
                      />
                      <Button
                        variant="secondary"
                        className="ml-auto px-3 py-1 text-xs"
                        loading={savingKey === key}
                        onClick={() => save(p.code, f.feature_key)}
                      >
                        Save
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
