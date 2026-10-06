"use client";

import { useEffect, useState } from "react";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { useAuth } from "@/lib/auth-context";
import { ApiError } from "@/lib/api";
import { notificationsApi, type NotificationOut, type Preferences } from "@/lib/notifications-api";

function Toggle({ label, hint, checked, onChange, disabled }: {
  label: string; hint?: string; checked: boolean; onChange: (v: boolean) => void; disabled?: boolean;
}) {
  return (
    <label className="flex items-start justify-between gap-4 rounded-xl border border-border bg-surface p-4">
      <span>
        <span className="block text-sm font-medium text-foreground">{label}</span>
        {hint && <span className="mt-0.5 block text-xs text-muted">{hint}</span>}
      </span>
      <input type="checkbox" checked={checked} disabled={disabled}
             onChange={(e) => onChange(e.target.checked)} className="mt-1 h-5 w-5" />
    </label>
  );
}

export default function SettingsPage() {
  const { authCall } = useAuth();
  const [prefs, setPrefs] = useState<Preferences | null>(null);
  const [notifs, setNotifs] = useState<NotificationOut[]>([]);
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function refreshNotifs() {
    try {
      setNotifs(await authCall((t) => notificationsApi.list(t)));
    } catch {
      /* ignore */
    }
  }

  useEffect(() => {
    authCall((t) => notificationsApi.preferences(t)).then(setPrefs).catch(() => setError("Could not load settings."));
    void refreshNotifs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (!prefs) return <p className="text-sm text-muted">Loading…</p>;

  async function save() {
    setError(null);
    setMsg(null);
    setSaving(true);
    try {
      const p = prefs!;
      const updated = await authCall((t) =>
        notificationsApi.updatePreferences(t, {
          full_name: p.full_name,
          phone_number: p.phone_number,
          whatsapp_opt_in: p.whatsapp_opt_in,
          email_opt_in: p.email_opt_in,
        }),
      );
      setPrefs(updated);
      setMsg("Preferences saved.");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not save.");
    } finally {
      setSaving(false);
    }
  }

  async function sendTest(channel: "whatsapp" | "email") {
    setError(null);
    setMsg(null);
    try {
      const res = await authCall((t) => notificationsApi.test(t, channel, "This is a Journey Junction test message."));
      setMsg(`Test ${channel} ${res.status}${res.status === "mock" ? " (no provider key configured — mock mode)" : ""}.`);
      await refreshNotifs();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Test failed.");
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-8">
      <h1 className="text-2xl font-bold text-foreground">Settings & notifications</h1>
      {msg && <Alert tone="success">{msg}</Alert>}
      {error && <Alert tone="error">{error}</Alert>}

      <section className="space-y-4">
        <Input label="Full name" value={prefs.full_name}
               onChange={(e) => setPrefs({ ...prefs, full_name: e.target.value })} />
        <Input label="WhatsApp phone number (with country code, e.g. +9715…)" value={prefs.phone_number}
               onChange={(e) => setPrefs({ ...prefs, phone_number: e.target.value })} placeholder="+971500000000" />

        <Toggle
          label="Email notifications"
          hint={prefs.email_enabled ? "Via Klaviyo" : "Server has no email provider configured yet — will run in mock mode."}
          checked={prefs.email_opt_in}
          onChange={(v) => setPrefs({ ...prefs, email_opt_in: v })}
        />
        <Toggle
          label="WhatsApp notifications"
          hint={prefs.whatsapp_enabled ? "Via WhatsApp Cloud API" : "Server has no WhatsApp token configured yet — will run in mock mode."}
          checked={prefs.whatsapp_opt_in}
          onChange={(v) => setPrefs({ ...prefs, whatsapp_opt_in: v })}
        />

        <div className="flex flex-wrap gap-3">
          <Button onClick={save} loading={saving}>Save preferences</Button>
          <Button variant="secondary" onClick={() => sendTest("whatsapp")}>Send test WhatsApp</Button>
          <Button variant="secondary" onClick={() => sendTest("email")}>Send test email</Button>
        </div>
      </section>

      <section>
        <h2 className="text-lg font-semibold text-foreground">Recent notifications</h2>
        {notifs.length === 0 ? (
          <p className="mt-2 text-sm text-muted">No notifications yet.</p>
        ) : (
          <div className="mt-3 space-y-1">
            {notifs.slice(0, 15).map((n) => (
              <div key={n.id} className="flex items-center justify-between rounded-lg border border-border bg-surface px-3 py-2 text-xs">
                <span className="font-medium text-foreground capitalize">{n.channel} · {n.event}</span>
                <span className="text-muted">
                  {n.status} · {new Date(n.created_at).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
