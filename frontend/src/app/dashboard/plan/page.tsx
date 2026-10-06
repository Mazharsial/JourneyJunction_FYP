"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { useAuth } from "@/lib/auth-context";
import { ApiError } from "@/lib/api";
import { locationApi, travelApi, type City } from "@/lib/travel-api";

function plusDays(n: number): string {
  const d = new Date();
  d.setDate(d.getDate() + n);
  return d.toISOString().slice(0, 10);
}

export default function PlanTripPage() {
  const router = useRouter();
  const { authCall } = useAuth();
  const [cities, setCities] = useState<City[]>([]);
  const [destination, setDestination] = useState("");
  const [origin, setOrigin] = useState("");
  const [start, setStart] = useState(plusDays(14));
  const [end, setEnd] = useState(plusDays(18));
  const [budget, setBudget] = useState("medium");
  const [purpose, setPurpose] = useState("tourism");
  const [travelers, setTravelers] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    locationApi
      .cities()
      .then((c) => {
        setCities(c);
        const dubai = c.find((x) => x.name === "Dubai");
        if (dubai) setDestination(dubai.id);
      })
      .catch(() => setError("Could not load cities. Is the API running?"));
  }, []);

  const isPilgrimage = purpose === "umrah" || purpose === "hajj";

  // Umrah/Hajj can only go to Saudi Arabia, so restrict the destination list.
  const destCities = useMemo(
    () => (isPilgrimage ? cities.filter((c) => c.country_iso2 === "SA") : cities),
    [cities, isPilgrimage],
  );
  const destOptions = useMemo(
    () => destCities.map((c) => ({ value: c.id, label: `${c.name} (${c.iata_code}) · ${c.country_iso2}` })),
    [destCities],
  );
  const cityOptions = useMemo(
    () => cities.map((c) => ({ value: c.id, label: `${c.name} (${c.iata_code}) · ${c.country_iso2}` })),
    [cities],
  );

  // When switching to/from a pilgrimage, keep the destination valid.
  function onPurposeChange(next: string) {
    setPurpose(next);
    if (next === "umrah" || next === "hajj") {
      const makkah = cities.find((c) => c.name === "Makkah");
      if (makkah) setDestination(makkah.id);
    } else {
      const dubai = cities.find((c) => c.name === "Dubai");
      if (dubai) setDestination(dubai.id);
    }
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!destination) {
      setError("Please choose a destination.");
      return;
    }
    setSubmitting(true);
    try {
      const trip = await authCall((t) =>
        travelApi.createTrip(t, {
          destination_city_id: destination,
          origin_city_id: origin || null,
          start_date: start,
          end_date: end,
          budget_tier: budget,
          purpose,
          travelers,
        }),
      );
      router.push(`/dashboard/trips/${trip.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create the trip. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="text-2xl font-bold text-foreground">Plan a trip</h1>
      <p className="mt-1 text-sm text-muted">
        Pick your destination and dates — we&apos;ll assemble flights, hotels and an itinerary.
      </p>

      <form onSubmit={onSubmit} className="mt-6 space-y-5 rounded-2xl border border-border bg-surface p-6">
        {error && <Alert tone="error">{error}</Alert>}
        <Select
          label="Trip purpose"
          options={[
            { value: "tourism", label: "Tourism" },
            { value: "umrah", label: "Umrah (pilgrimage)" },
            { value: "hajj", label: "Hajj (pilgrimage)" },
          ]}
          value={purpose}
          onChange={(e) => onPurposeChange(e.target.value)}
        />
        {isPilgrimage && (
          <Alert tone="info">
            {purpose === "umrah" ? "Umrah" : "Hajj"} trips go to Saudi Arabia (Makkah, Madinah or
            Jeddah). You&apos;ll see pilgrimage-specific requirements — Nusuk visa, mandatory
            vaccinations and more — on the trip page.
          </Alert>
        )}
        <Select
          label="Destination"
          options={destOptions}
          placeholder="Choose a city"
          value={destination}
          onChange={(e) => setDestination(e.target.value)}
          required
        />
        <Select
          label="Origin (optional)"
          options={cityOptions}
          placeholder="Where are you flying from?"
          value={origin}
          onChange={(e) => setOrigin(e.target.value)}
        />
        <div className="grid gap-4 sm:grid-cols-2">
          <Input label="Start date" type="date" value={start} onChange={(e) => setStart(e.target.value)} required />
          <Input label="End date" type="date" value={end} onChange={(e) => setEnd(e.target.value)} required />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <Select
            label="Budget"
            options={[
              { value: "low", label: "Low" },
              { value: "medium", label: "Medium" },
              { value: "luxury", label: "Luxury" },
            ]}
            value={budget}
            onChange={(e) => setBudget(e.target.value)}
          />
          <Input
            label="Travelers"
            type="number"
            min={1}
            max={20}
            value={travelers}
            onChange={(e) => setTravelers(Math.max(1, Number(e.target.value) || 1))}
          />
        </div>
        <Button type="submit" full loading={submitting}>
          Create trip plan
        </Button>
      </form>
    </div>
  );
}
