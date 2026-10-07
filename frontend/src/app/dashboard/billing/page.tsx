"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { useAuth } from "@/lib/auth-context";
import { ApiError } from "@/lib/api";
import {
  billingApi,
  featureLabel,
  featureValue,
  type PlansResponse,
  type SubscriptionOut,
} from "@/lib/billing-api";

function price(cents: number, currency: string) {
  if (cents === 0) return "Free";
  return `${currency === "USD" ? "$" : currency + " "}${(cents / 100).toFixed(2)}`;
}

function BillingInner() {
  const { authCall } = useAuth();
  const params = useSearchParams();
  const [data, setData] = useState<PlansResponse | null>(null);
  const [sub, setSub] = useState<SubscriptionOut | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const status = params.get("status");

  useEffect(() => {
    billingApi.plans().then(setData).catch(() => setError("Could not load plans."));
    authCall((t) => billingApi.subscription(t)).then(setSub).catch(() => {});
  }, [authCall]);

  async function upgrade(planCode: string) {
    setError(null);
    setBusy(planCode);
    try {
      const { url } = await authCall((t) => billingApi.checkout(t, planCode));
      window.location.href = url; // redirect to Stripe Checkout
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.code === "billing_unconfigured"
            ? "Billing isn't configured on the server yet (set STRIPE_SECRET_KEY)."
            : err.message
          : "Could not start checkout.",
      );
      setBusy(null);
    }
  }

  async function manage() {
    setError(null);
    setBusy("portal");
    try {
      const { url } = await authCall((t) => billingApi.portal(t));
      window.location.href = url;
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not open billing portal.");
      setBusy(null);
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Subscription & billing</h1>
        {sub && (
          <p className="mt-1 text-sm text-muted">
            Current plan: <span className="font-semibold text-foreground">{sub.plan_name}</span>{" "}
            <span className="capitalize">({sub.status})</span>
          </p>
        )}
      </div>

      {status === "success" && <Alert tone="success">Payment successful — your plan will update shortly.</Alert>}
      {status === "cancel" && <Alert tone="info">Checkout canceled. You can upgrade anytime.</Alert>}
      {error && <Alert tone="error">{error}</Alert>}

      {sub && sub.usage.length > 0 && (
        <section className="rounded-2xl border border-border bg-surface p-5">
          <h2 className="text-sm font-semibold text-foreground">This month&apos;s usage</h2>
          <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
            {sub.usage
              .filter((u) => u.limit !== -1 && u.limit !== 0)
              .map((u) => (
                <div key={u.feature}>
                  <div className="flex justify-between text-xs text-muted">
                    <span>{featureLabel(u.feature)}</span>
                    <span>
                      {u.used} / {u.limit}
                    </span>
                  </div>
                  <div className="mt-1 h-2 overflow-hidden rounded-full bg-surface-muted">
                    <div
                      className="h-full brand-gradient"
                      style={{ width: `${Math.min(100, (u.used / u.limit) * 100)}%` }}
                    />
                  </div>
                </div>
              ))}
          </div>
        </section>
      )}

      {!data ? (
        <p className="text-sm text-muted">Loading plans…</p>
      ) : (
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
          {data.plans.map((p) => {
            const current = sub?.plan_code === p.code;
            return (
              <div
                key={p.code}
                className={`flex flex-col rounded-2xl border bg-surface p-6 ${
                  p.code === "pro" ? "border-teal ring-1 ring-teal/30" : "border-border"
                }`}
              >
                <h3 className="text-lg font-bold text-foreground">{p.name}</h3>
                <p className="mt-1 text-sm text-muted">{p.description}</p>
                <p className="mt-4 text-2xl font-bold text-foreground">
                  {price(p.price_cents, p.currency)}
                  {p.price_cents > 0 && <span className="text-sm font-normal text-muted">/{p.interval}</span>}
                </p>
                <ul className="mt-4 flex-1 space-y-2 text-sm">
                  {p.features.map((f) => (
                    <li key={f.feature_key} className="flex justify-between gap-3 text-muted">
                      <span>{featureLabel(f.feature_key)}</span>
                      <span className="font-medium text-foreground">{featureValue(f)}</span>
                    </li>
                  ))}
                </ul>
                <div className="mt-5">
                  {current ? (
                    <Button variant="secondary" full disabled>
                      Current plan
                    </Button>
                  ) : p.purchasable ? (
                    <Button full loading={busy === p.code} onClick={() => upgrade(p.code)}>
                      Upgrade to {p.name}
                    </Button>
                  ) : (
                    <Button variant="secondary" full disabled>
                      {p.code === "free" ? "Included" : "Unavailable"}
                    </Button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {sub && sub.plan_code !== "free" && (
        <div>
          <Button variant="secondary" loading={busy === "portal"} onClick={manage}>
            Manage billing
          </Button>
        </div>
      )}
    </div>
  );
}

export default function BillingPage() {
  return (
    <Suspense fallback={<p className="text-sm text-muted">Loading…</p>}>
      <BillingInner />
    </Suspense>
  );
}
