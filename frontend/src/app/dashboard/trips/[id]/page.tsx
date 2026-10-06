"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Alert } from "@/components/ui/Alert";
import { useAuth } from "@/lib/auth-context";
import { travelApi, type TripDetail, type FlightOffer, type HotelOffer } from "@/lib/travel-api";

function money(amount: number, currency: string) {
  return `${currency} ${amount.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}
function time(iso: string) {
  const d = new Date(iso);
  return isNaN(d.getTime()) ? iso : d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}
function dur(mins: number) {
  return `${Math.floor(mins / 60)}h ${mins % 60}m`;
}

function FlightCard({ f }: { f: FlightOffer }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-4">
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold text-foreground">{f.airline}</span>
        <span className="text-sm font-bold text-brand-blue">{money(f.price_amount, f.price_currency)}</span>
      </div>
      <p className="mt-1 text-xs text-muted">
        {f.origin_iata} {time(f.depart_time)} → {f.destination_iata} {time(f.arrive_time)} · {dur(f.duration_minutes)} ·{" "}
        {f.stops === 0 ? "Non-stop" : `${f.stops} stop`}
      </p>
      <span className="mt-2 inline-block rounded-full bg-surface-muted px-2 py-0.5 text-[11px] text-muted">
        {f.cabin} · {f.flight_number}
      </span>
    </div>
  );
}

function HotelCard({ h }: { h: HotelOffer }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-4">
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold text-foreground">{h.name}</span>
        <span className="text-xs font-medium text-warning">★ {h.rating.toFixed(1)}</span>
      </div>
      <p className="mt-1 text-xs text-muted">{h.address}</p>
      <p className="mt-2 text-sm font-bold text-brand-blue">
        {money(h.price_per_night, h.price_currency)}
        <span className="text-xs font-normal text-muted"> / night · {money(h.total_amount, h.price_currency)} total</span>
      </p>
      <div className="mt-2 flex flex-wrap gap-1">
        {h.amenities.slice(0, 4).map((a) => (
          <span key={a} className="rounded-full bg-surface-muted px-2 py-0.5 text-[10px] text-muted">{a}</span>
        ))}
      </div>
    </div>
  );
}

export default function TripDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { authCall } = useAuth();
  const [data, setData] = useState<TripDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    authCall((t) => travelApi.getTrip(t, id))
      .then(setData)
      .catch(() => setError("Trip not found."));
  }, [id, authCall]);

  if (error) {
    return (
      <div>
        <Alert tone="error">{error}</Alert>
        <Link href="/dashboard/trips" className="mt-4 inline-block text-sm text-brand-blue hover:underline">
          ← Back to trips
        </Link>
      </div>
    );
  }
  if (!data) return <p className="text-sm text-muted">Loading trip…</p>;

  const { trip, itinerary, suggested_flights, suggested_hotels, visa } = data;

  return (
    <div className="space-y-8">
      <div>
        <Link href="/dashboard/trips" className="text-sm text-brand-blue hover:underline">← My trips</Link>
        <h1 className="mt-2 text-2xl font-bold text-foreground">{trip.title}</h1>
        <p className="mt-1 text-sm text-muted">
          {trip.origin ? `${trip.origin.name} → ` : ""}{trip.destination.name} · {trip.start_date} → {trip.end_date} ·{" "}
          <span className="capitalize">{trip.budget_tier}</span> · {trip.travelers} traveler{trip.travelers > 1 ? "s" : ""}
        </p>
      </div>

      {visa && (
        <Alert tone="info">
          <strong className="capitalize">Visa: {visa.requirement.replace(/_/g, " ")}</strong>
          {visa.allowed_stay_days ? ` · up to ${visa.allowed_stay_days} days` : ""} — {visa.notes}
          <span className="mt-1 block text-xs opacity-80">{visa.disclaimer}</span>
        </Alert>
      )}

      <section>
        <h2 className="text-lg font-semibold text-foreground">Itinerary</h2>
        <ol className="mt-4 space-y-3">
          {itinerary.map((d) => (
            <li key={d.day_number} className="flex gap-4 rounded-xl border border-border bg-surface p-4">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full brand-gradient text-sm font-bold text-white">
                {d.day_number}
              </div>
              <div>
                <p className="text-sm font-semibold text-foreground">{d.title}</p>
                <p className="text-xs text-muted">{d.date} — {d.notes}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      {suggested_flights.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-foreground">Suggested flights</h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {suggested_flights.map((f, i) => <FlightCard key={i} f={f} />)}
          </div>
        </section>
      )}

      <section>
        <h2 className="text-lg font-semibold text-foreground">Suggested hotels</h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          {suggested_hotels.map((h, i) => <HotelCard key={i} h={h} />)}
        </div>
      </section>
    </div>
  );
}
