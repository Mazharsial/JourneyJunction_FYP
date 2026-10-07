"use client";
/* eslint-disable @next/next/no-img-element */

import Link from "next/link";
import { motion } from "framer-motion";
import { useAuth } from "@/lib/auth-context";
import { Alert } from "@/components/ui/Alert";

type Tile = { title: string; body: string; href: string; icon: string; img: string; accent: string };

const IMG = (id: string) => `https://images.unsplash.com/${id}?auto=format&fit=crop&w=640&q=60`;

const tiles: Tile[] = [
  {
    title: "Plan a trip",
    body: "Enter a destination and get flights, hotels and a day-by-day itinerary.",
    href: "/dashboard/plan",
    icon: "🧭",
    img: IMG("photo-1512453979798-5ea266f8880c"), // Dubai
    accent: "from-sky-500/70",
  },
  {
    title: "AI assistant",
    body: "Ask about visas, routes and requirements — grounded, honest answers.",
    href: "/dashboard/assistant",
    icon: "🤖",
    img: IMG("photo-1526378722484-bd91ca387e72"), // tech
    accent: "from-violet-500/70",
  },
  {
    title: "Verify documents",
    body: "Upload a passport or visa — AI OCR catches errors and missing fields.",
    href: "/dashboard/documents",
    icon: "🛡️",
    img: IMG("photo-1569429593410-b498b3fb3387"), // passport
    accent: "from-emerald-500/70",
  },
  {
    title: "My trips",
    body: "View and manage your saved trips, requirements and bookings.",
    href: "/dashboard/trips",
    icon: "🧳",
    img: IMG("photo-1436491865332-7a61a109cc05"), // airplane
    accent: "from-cyan-500/70",
  },
  {
    title: "Subscription",
    body: "View your plan, usage and upgrade for more AI and document checks.",
    href: "/dashboard/billing",
    icon: "💳",
    img: IMG("photo-1554224155-6726b3ff858f"), // finance
    accent: "from-amber-500/70",
  },
];

export default function DashboardHome() {
  const { user } = useAuth();
  if (!user) return null;

  return (
    <div className="space-y-8">
      {/* welcome banner */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative overflow-hidden rounded-3xl border border-border"
      >
        <img
          src={IMG("photo-1512453979798-5ea266f8880c")}
          alt=""
          className="absolute inset-0 h-full w-full object-cover"
          loading="lazy"
        />
        <div className="absolute inset-0 brand-gradient opacity-85" />
        <div className="relative px-6 py-8 text-white sm:px-10 sm:py-10">
          <h1 className="text-2xl font-bold sm:text-3xl">
            Welcome{user.full_name ? `, ${user.full_name}` : ""} 👋
          </h1>
          <p className="mt-2 max-w-xl text-sm text-white/90">
            Plan a trip, chat with the AI assistant, verify your documents and track every travel
            requirement — all in one place.
          </p>
          <div className="mt-5 flex flex-wrap gap-3">
            <Link href="/dashboard/plan" className="rounded-xl bg-white px-5 py-2.5 text-sm font-semibold text-navy shadow transition hover:opacity-90">
              Plan a trip
            </Link>
            <Link href="/dashboard/assistant" className="rounded-xl border border-white/40 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-white/10">
              Ask the AI assistant
            </Link>
          </div>
        </div>
      </motion.div>

      {!user.is_verified && (
        <Alert tone="info">
          Your email isn&apos;t verified yet. You can verify it from Settings once you receive the link.
        </Alert>
      )}

      <div>
        <h2 className="text-lg font-semibold text-foreground">What would you like to do?</h2>
        <div className="mt-4 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {tiles.map((t, i) => (
            <motion.div
              key={t.title}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 + i * 0.07, duration: 0.4 }}
              whileHover={{ y: -6 }}
            >
              <Link
                href={t.href}
                className="group block overflow-hidden rounded-2xl border border-border bg-surface shadow-sm transition hover:shadow-xl"
              >
                <div className={`relative h-32 bg-gradient-to-br ${t.accent} to-transparent`}>
                  <img
                    src={t.img}
                    alt=""
                    className="absolute inset-0 h-full w-full object-cover transition duration-500 group-hover:scale-105"
                    loading="lazy"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
                  <span className="absolute bottom-2 left-3 flex h-9 w-9 items-center justify-center rounded-xl bg-white/90 text-lg shadow">
                    {t.icon}
                  </span>
                </div>
                <div className="p-4">
                  <h3 className="text-sm font-semibold text-foreground">{t.title}</h3>
                  <p className="mt-1.5 text-xs leading-relaxed text-muted">{t.body}</p>
                  <span className="mt-3 inline-block text-xs font-semibold text-brand-blue transition group-hover:translate-x-1">
                    Open →
                  </span>
                </div>
              </Link>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}
