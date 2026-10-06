"use client";

import { motion } from "framer-motion";

const features = [
  {
    title: "Destination-based planning",
    body: "Type where you want to go. Get flights, hotels and a day-by-day itinerary in one place.",
    icon: "🧭",
  },
  {
    title: "Flight & hotel comparison",
    body: "Real-time options with prices, schedules, ratings and amenities — compared for you.",
    icon: "✈️",
  },
  {
    title: "Budget-aware recommendations",
    body: "Low, medium or luxury — the plan adapts to the budget you choose.",
    icon: "💳",
  },
  {
    title: "AI travel assistant",
    body: "Ask anything about visas, routes or requirements. Grounded answers, honest when unsure.",
    icon: "🤖",
  },
  {
    title: "AI document verification",
    body: "Upload a passport or visa form. OCR + AI catch spelling, missing fields and mismatches — and suggest fixes.",
    icon: "🛡️",
    highlight: true,
  },
  {
    title: "Compliance checking",
    body: "Checks your documents against the destination's travel/visa requirements before you go.",
    icon: "✅",
  },
];

export function Features() {
  return (
    <section id="features" className="mx-auto max-w-6xl px-4 py-20">
      <div className="mx-auto max-w-2xl text-center">
        <h2 className="text-3xl font-bold tracking-tight text-foreground md:text-4xl">
          Everything your trip needs — intelligently
        </h2>
        <p className="mt-4 text-muted">
          One platform replaces a dozen tabs and the travel agent.
        </p>
      </div>

      <div className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {features.map((f, i) => (
          <motion.article
            key={f.title}
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, delay: 0.05 + (i % 3) * 0.06 }}
            className={`rounded-2xl border bg-surface p-6 transition hover:-translate-y-1 hover:shadow-lg ${
              f.highlight ? "border-teal ring-1 ring-teal/30" : "border-border"
            }`}
          >
            <div className="text-2xl">{f.icon}</div>
            <h3 className="mt-4 text-lg font-semibold text-foreground">{f.title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-muted">{f.body}</p>
            {f.highlight && (
              <span className="mt-4 inline-block rounded-full bg-teal/10 px-3 py-1 text-xs font-semibold text-teal">
                Our unique feature
              </span>
            )}
          </motion.article>
        ))}
      </div>
    </section>
  );
}
