"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { useAuth } from "@/lib/auth-context";
import { travelApi, type TripOut } from "@/lib/travel-api";

export default function TripsPage() {
  const { authCall } = useAuth();
  const [trips, setTrips] = useState<TripOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    authCall((t) => travelApi.listTrips(t))
      .then(setTrips)
      .catch(() => setError("Could not load your trips."));
  }, [authCall]);

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-foreground">My trips</h1>
        <Link href="/dashboard/plan">
          <Button>Plan a trip</Button>
        </Link>
      </div>

      {error && <div className="mt-6"><Alert tone="error">{error}</Alert></div>}

      {trips === null && !error && <p className="mt-6 text-sm text-muted">Loading…</p>}

      {trips && trips.length === 0 && (
        <div className="mt-10 rounded-2xl border border-dashed border-border p-10 text-center">
          <p className="text-muted">No trips yet.</p>
          <Link href="/dashboard/plan" className="mt-3 inline-block">
            <Button>Plan your first trip</Button>
          </Link>
        </div>
      )}

      {trips && trips.length > 0 && (
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {trips.map((t) => (
            <Link
              key={t.id}
              href={`/dashboard/trips/${t.id}`}
              className="rounded-2xl border border-border bg-surface p-5 transition hover:-translate-y-1 hover:shadow-lg"
            >
              <h3 className="font-semibold text-foreground">{t.title}</h3>
              <p className="mt-1 text-sm text-muted">
                {t.origin ? `${t.origin.name} → ` : ""}
                {t.destination.name}
              </p>
              <p className="mt-2 text-xs text-muted">
                {t.start_date} → {t.end_date} · {t.travelers} traveler{t.travelers > 1 ? "s" : ""}
              </p>
              <span className="mt-3 inline-block rounded-full bg-surface-muted px-2.5 py-0.5 text-[11px] font-medium capitalize text-muted">
                {t.budget_tier}
              </span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
