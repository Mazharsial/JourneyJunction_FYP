"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { billingApi, featureLabel, featureValue, type PlanOut } from "@/lib/billing-api";

function price(cents: number, currency: string) {
  if (cents === 0) return "Free";
  return `${currency === "USD" ? "$" : currency + " "}${(cents / 100).toFixed(2)}`;
}

export function PricingSection() {
  const [plans, setPlans] = useState<PlanOut[] | null>(null);

  useEffect(() => {
    billingApi.plans().then((r) => setPlans(r.plans)).catch(() => setPlans([]));
  }, []);

  return (
    <section id="pricing" className="mx-auto max-w-6xl px-4 py-20">
      <div className="mx-auto max-w-2xl text-center">
        <h2 className="text-3xl font-bold tracking-tight text-foreground md:text-4xl">
          Simple, transparent pricing
        </h2>
        <p className="mt-4 text-muted">
          Start free. Upgrade when you need more AI and document checks.
        </p>
      </div>

      {!plans ? (
        <p className="mt-10 text-center text-sm text-muted">Loading plans…</p>
      ) : (
        <div className="mt-12 grid grid-cols-1 gap-6 lg:grid-cols-3">
          {plans.map((p) => (
            <div
              key={p.code}
              className={`flex flex-col rounded-2xl border bg-surface p-6 ${
                p.code === "pro" ? "border-teal ring-1 ring-teal/30 shadow-lg" : "border-border"
              }`}
            >
              {p.code === "pro" && (
                <span className="mb-3 self-start rounded-full bg-teal/10 px-3 py-1 text-xs font-semibold text-teal">
                  Most popular
                </span>
              )}
              <h3 className="text-lg font-bold text-foreground">{p.name}</h3>
              <p className="mt-1 text-sm text-muted">{p.description}</p>
              <p className="mt-4 text-3xl font-bold text-foreground">
                {price(p.price_cents, p.currency)}
                {p.price_cents > 0 && <span className="text-sm font-normal text-muted">/{p.interval}</span>}
              </p>
              <ul className="mt-5 flex-1 space-y-2 text-sm">
                {p.features.map((f) => (
                  <li key={f.feature_key} className="flex justify-between gap-3 text-muted">
                    <span>{featureLabel(f.feature_key)}</span>
                    <span className="font-medium text-foreground">{featureValue(f)}</span>
                  </li>
                ))}
              </ul>
              <Link
                href="/register"
                className={`mt-6 rounded-xl px-5 py-2.5 text-center text-sm font-semibold transition ${
                  p.code === "pro"
                    ? "brand-gradient text-white hover:opacity-90"
                    : "border border-border text-foreground hover:bg-surface-muted"
                }`}
              >
                {p.code === "free" ? "Get started free" : `Choose ${p.name}`}
              </Link>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
