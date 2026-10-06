"use client";

import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { useAuth } from "@/lib/auth-context";
import { adminApi, type VisaRule } from "@/lib/admin-api";

const REQUIREMENTS = ["visa_required", "visa_on_arrival", "e_visa", "visa_free"];

const empty = {
  origin: "",
  destination: "",
  requirement: "visa_required",
  allowed_stay_days: "",
  notes: "",
  source: "",
};

export function VisaRulesManager() {
  const { authCall } = useAuth();
  const [rules, setRules] = useState<VisaRule[] | null>(null);
  const [form, setForm] = useState({ ...empty });
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      setRules(await authCall((t) => adminApi.visaRules(t)));
    } catch {
      setError("Could not load visa rules.");
    }
  }, [authCall]);

  useEffect(() => {
    void load();
  }, [load]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (form.origin.length !== 2 || form.destination.length !== 2) {
      setError("Origin and destination must be 2-letter ISO codes (e.g. PK, AE, SA).");
      return;
    }
    setBusy(true);
    try {
      await authCall((t) =>
        adminApi.upsertVisaRule(t, {
          origin: form.origin.toUpperCase(),
          destination: form.destination.toUpperCase(),
          requirement: form.requirement,
          allowed_stay_days: form.allowed_stay_days ? parseInt(form.allowed_stay_days, 10) : null,
          notes: form.notes,
          source: form.source,
        }),
      );
      setForm({ ...empty });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed.");
    } finally {
      setBusy(false);
    }
  }

  async function remove(id: string) {
    setError(null);
    try {
      await authCall((t) => adminApi.deleteVisaRule(t, id));
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed.");
    }
  }

  const inputCls =
    "rounded-lg border border-border bg-surface px-3 py-1.5 text-sm outline-none focus:border-teal";

  return (
    <section>
      <h2 className="text-lg font-semibold text-foreground">Visa rules</h2>
      <p className="mt-1 text-xs text-muted">
        Informational visa guidance shown on trips. Upsert by origin + destination.
      </p>
      {error && <div className="mt-3"><Alert tone="error">{error}</Alert></div>}

      <form onSubmit={submit} className="mt-4 grid gap-2 rounded-xl border border-border bg-surface p-4 sm:grid-cols-6">
        <input className={inputCls} placeholder="Origin (PK)" maxLength={2}
          value={form.origin} onChange={(e) => setForm({ ...form, origin: e.target.value })} />
        <input className={inputCls} placeholder="Dest (SA)" maxLength={2}
          value={form.destination} onChange={(e) => setForm({ ...form, destination: e.target.value })} />
        <select className={inputCls} value={form.requirement}
          onChange={(e) => setForm({ ...form, requirement: e.target.value })}>
          {REQUIREMENTS.map((r) => <option key={r} value={r}>{r.replace(/_/g, " ")}</option>)}
        </select>
        <input className={inputCls} type="number" min={0} placeholder="Stay days"
          value={form.allowed_stay_days} onChange={(e) => setForm({ ...form, allowed_stay_days: e.target.value })} />
        <input className={`${inputCls} sm:col-span-2`} placeholder="Notes"
          value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
        <Button type="submit" loading={busy} className="px-4 py-1.5 sm:col-span-6">Add / update rule</Button>
      </form>

      <div className="mt-3 overflow-x-auto rounded-xl border border-border">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-surface-muted text-left text-xs text-muted">
              <th className="px-3 py-2">Route</th>
              <th className="px-3 py-2">Requirement</th>
              <th className="px-3 py-2">Stay</th>
              <th className="px-3 py-2">Notes</th>
              <th className="px-3 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {rules?.length === 0 && (
              <tr><td colSpan={5} className="px-3 py-3 text-muted">No visa rules.</td></tr>
            )}
            {rules?.map((r) => (
              <tr key={r.id} className="border-t border-border">
                <td className="px-3 py-2 font-medium text-foreground">{r.origin_iso2} → {r.destination_iso2}</td>
                <td className="px-3 py-2 capitalize text-muted">{r.requirement.replace(/_/g, " ")}</td>
                <td className="px-3 py-2 text-muted">{r.allowed_stay_days ?? "—"}</td>
                <td className="px-3 py-2 text-muted">{r.notes}</td>
                <td className="px-3 py-2 text-right">
                  <button onClick={() => remove(r.id)} className="text-xs font-medium text-error hover:underline">
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
