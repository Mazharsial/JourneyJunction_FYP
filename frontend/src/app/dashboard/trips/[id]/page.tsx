"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Alert } from "@/components/ui/Alert";
import { useAuth } from "@/lib/auth-context";
import {
  travelApi,
  type TripDetail,
  type FlightOffer,
  type HotelOffer,
  type TravelRequirements,
} from "@/lib/travel-api";

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
      <div className="flex items-center justify-between gap-2">
        <span className="min-w-0 truncate text-sm font-semibold text-foreground">{f.airline}</span>
        <span className="shrink-0 text-sm font-bold text-brand-blue">{money(f.price_amount, f.price_currency)}</span>
      </div>
      <p className="mt-1 text-xs text-muted">
        {f.origin_iata} {time(f.depart_time)} → {f.destination_iata} {time(f.arrive_time)} · {dur(f.duration_minutes)} ·{" "}
        {f.stops === 0 ? "Non-stop" : `${f.stops} stop`}
      </p>
      <div className="mt-2 flex items-center justify-between">
        <span className="inline-block rounded-full bg-surface-muted px-2 py-0.5 text-[11px] text-muted">
          {f.cabin} · {f.flight_number}
        </span>
        {f.booking_url && (
          <a href={f.booking_url} target="_blank" rel="noopener noreferrer"
             className="text-xs font-semibold text-brand-blue hover:underline">
            Book / verify →
          </a>
        )}
      </div>
    </div>
  );
}

function HotelCard({ h }: { h: HotelOffer }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-4">
      <div className="flex items-start justify-between gap-2">
        <span className="min-w-0 break-words text-sm font-semibold text-foreground">{h.name}</span>
        <span className="shrink-0 text-xs font-medium text-warning">★ {h.rating.toFixed(1)}</span>
      </div>
      <p className="mt-1 break-words text-xs text-muted">{h.address}</p>
      <p className="mt-2 text-sm font-bold text-brand-blue">
        {money(h.price_per_night, h.price_currency)}
        <span className="text-xs font-normal text-muted"> / night · {money(h.total_amount, h.price_currency)} total</span>
      </p>
      <div className="mt-2 flex flex-wrap gap-1">
        {h.amenities.slice(0, 4).map((a) => (
          <span key={a} className="rounded-full bg-surface-muted px-2 py-0.5 text-[10px] text-muted">{a}</span>
        ))}
      </div>
      {h.booking_url && (
        <a href={h.booking_url} target="_blank" rel="noopener noreferrer"
           className="mt-2 inline-block text-xs font-semibold text-brand-blue hover:underline">
          Book / verify →
        </a>
      )}
    </div>
  );
}

function InfoBlock({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-4">
      <h3 className="text-sm font-semibold text-foreground">{title}</h3>
      <div className="mt-2 text-sm text-muted">{children}</div>
    </div>
  );
}

function RequirementsSection({ req }: { req: TravelRequirements }) {
  return (
    <section>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-semibold text-foreground">
          Travel requirements for {req.destination_country}
          {req.purpose && req.purpose !== "tourism" && (
            <span className="ml-2 rounded-full bg-ai/10 px-2 py-0.5 text-xs font-semibold uppercase text-ai">
              {req.purpose}
            </span>
          )}
        </h2>
        {req.documents_required > 0 && (
          <span
            className={`rounded-full px-3 py-1 text-xs font-semibold ${
              req.documents_ready >= req.documents_required
                ? "bg-success/10 text-success"
                : "bg-warning/10 text-warning"
            }`}
          >
            {req.documents_ready}/{req.documents_required} documents verified
          </span>
        )}
      </div>

      {req.visa && (
        <div className="mt-4">
          <Alert tone="info">
            <strong className="capitalize">Visa: {req.visa.requirement.replace(/_/g, " ")}</strong>
            {req.visa.allowed_stay_days ? ` · up to ${req.visa.allowed_stay_days} days` : ""} — {req.visa.notes}
          </Alert>
        </div>
      )}

      <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
        <InfoBlock title="Required documents">
          <ul className="space-y-2">
            {req.required_documents.map((doc, i) => {
              const icon =
                doc.status === "verified" ? "✓" : doc.status === "not_verified" ? "！" : "•";
              const color =
                doc.status === "verified"
                  ? "text-success"
                  : doc.status === "not_verified"
                  ? "text-warning"
                  : "text-muted";
              return (
                <li key={i} className="flex items-start gap-2">
                  <span className={`mt-0.5 shrink-0 font-bold ${color}`}>{icon}</span>
                  <span className="text-foreground">
                    {doc.label}
                    {doc.status === "verified" && (
                      <span className="ml-2 text-xs font-medium text-success">verified</span>
                    )}
                    {doc.status === "not_verified" && (
                      <Link href="/dashboard/documents" className="ml-2 text-xs font-medium text-brand-blue hover:underline">
                        verify now →
                      </Link>
                    )}
                  </span>
                </li>
              );
            })}
          </ul>
        </InfoBlock>

        <InfoBlock title="Passport & entry">
          <p>Passport must be valid for at least <strong className="text-foreground">{req.passport_validity_months} months</strong> beyond arrival.</p>
          {req.entry_notes && <p className="mt-2">{req.entry_notes}</p>}
        </InfoBlock>

        {req.health.length > 0 && (
          <InfoBlock title="Health & vaccinations">
            <ul className="list-disc space-y-1 pl-4">
              {req.health.map((h, i) => <li key={i}>{h}</li>)}
            </ul>
          </InfoBlock>
        )}

        {req.currency_notes && <InfoBlock title="Currency & cash">{req.currency_notes}</InfoBlock>}
        {req.customs_notes && <InfoBlock title="Customs">{req.customs_notes}</InfoBlock>}
        {req.emergency_number && <InfoBlock title="Emergency numbers">{req.emergency_number}</InfoBlock>}
      </div>

      {req.visa_types.length > 0 && (
        <div className="mt-6">
          <h3 className="text-base font-semibold text-foreground">Visa types & routes</h3>
          <p className="mt-1 text-xs text-muted">
            Available visa options for this destination. Fees are indicative — confirm at the official link below.
          </p>
          <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">
            {req.visa_types.map((v, i) => (
              <div key={i} className="rounded-xl border border-border bg-surface p-4">
                <div className="flex items-start justify-between gap-2">
                  <h4 className="text-sm font-semibold text-foreground">{v.name}</h4>
                  {v.fee && (
                    <span className="shrink-0 rounded-full bg-teal/10 px-2.5 py-0.5 text-xs font-semibold text-teal">
                      {v.fee}
                    </span>
                  )}
                </div>
                <div className="mt-1.5 flex flex-wrap gap-2">
                  {v.duration && (
                    <span className="rounded-full bg-surface-muted px-2.5 py-0.5 text-xs text-muted">⏳ {v.duration}</span>
                  )}
                  {v.entry && (
                    <span className="rounded-full bg-surface-muted px-2.5 py-0.5 text-xs text-muted">🎟 {v.entry}</span>
                  )}
                </div>
                {v.notes && <p className="mt-2 text-sm text-muted">{v.notes}</p>}
              </div>
            ))}
          </div>
        </div>
      )}

      {req.preparation.length > 0 && (
        <div className="mt-6">
          <h3 className="text-base font-semibold text-foreground">How to prepare — step by step</h3>
          <p className="mt-1 text-xs text-muted">
            From documents to visa to departure. Fees and timelines are indicative — verify at the official links.
          </p>
          <ol className="mt-4 space-y-3">
            {req.preparation.map((s, i) => (
              <li key={i} className="relative rounded-xl border border-border bg-surface p-4 pl-5">
                <span className="absolute left-0 top-0 h-full w-1 rounded-l-xl brand-gradient" aria-hidden />
                <p className="text-sm font-semibold text-foreground">{s.title}</p>
                {s.detail && <p className="mt-1 text-sm text-muted">{s.detail}</p>}
                <div className="mt-2 flex flex-wrap items-center gap-2">
                  {s.fee && (
                    <span className="rounded-full bg-surface-muted px-2.5 py-0.5 text-xs text-muted">
                      💳 {s.fee}
                    </span>
                  )}
                  {s.timeline && (
                    <span className="rounded-full bg-surface-muted px-2.5 py-0.5 text-xs text-muted">
                      ⏱ {s.timeline}
                    </span>
                  )}
                  {s.url && (
                    <a href={s.url} target="_blank" rel="noopener noreferrer"
                       className="ml-auto text-xs font-semibold text-brand-blue hover:underline">
                      Official info →
                    </a>
                  )}
                </div>
              </li>
            ))}
          </ol>
        </div>
      )}

      <div className="mt-6 flex flex-wrap items-center justify-between gap-2">
        {req.official_source && (
          <a href={req.official_source} target="_blank" rel="noopener noreferrer"
             className="text-sm font-medium text-brand-blue hover:underline">
            Official source →
          </a>
        )}
      </div>
      <p className="mt-2 text-xs text-muted">{req.disclaimer}</p>
    </section>
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

  const { trip, itinerary, suggested_flights, suggested_hotels, visa, requirements } = data;

  return (
    <div className="space-y-8">
      <div>
        <Link href="/dashboard/trips" className="text-sm text-brand-blue hover:underline">← My trips</Link>
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <h1 className="text-2xl font-bold text-foreground">{trip.title}</h1>
          {trip.purpose && trip.purpose !== "tourism" && (
            <span className="rounded-full bg-ai/10 px-2.5 py-1 text-xs font-semibold uppercase text-ai">
              {trip.purpose}
            </span>
          )}
        </div>
        <p className="mt-1 text-sm text-muted">
          {trip.origin ? `${trip.origin.name} → ` : ""}{trip.destination.name} · {trip.start_date} → {trip.end_date} ·{" "}
          <span className="capitalize">{trip.budget_tier}</span> · {trip.travelers} traveler{trip.travelers > 1 ? "s" : ""}
        </p>
      </div>

      {requirements ? (
        <RequirementsSection req={requirements} />
      ) : (
        visa && (
          <Alert tone="info">
            <strong className="capitalize">Visa: {visa.requirement.replace(/_/g, " ")}</strong>
            {visa.allowed_stay_days ? ` · up to ${visa.allowed_stay_days} days` : ""} — {visa.notes}
            <span className="mt-1 block text-xs opacity-80">{visa.disclaimer}</span>
          </Alert>
        )
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
          <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
            {suggested_flights.map((f, i) => <FlightCard key={i} f={f} />)}
          </div>
        </section>
      )}

      <section>
        <h2 className="text-lg font-semibold text-foreground">Suggested hotels</h2>
        {suggested_hotels.some((h) => h.provider === "geoapify") && (
          <p className="mt-1 text-xs text-muted">
            Hotel names and locations are live; prices and ratings are estimates.
          </p>
        )}
        <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
          {suggested_hotels.map((h, i) => <HotelCard key={i} h={h} />)}
        </div>
      </section>
    </div>
  );
}
