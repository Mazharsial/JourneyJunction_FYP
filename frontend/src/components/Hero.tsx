"use client";

import { motion, type Variants } from "framer-motion";
import Link from "next/link";
import { brand } from "@/lib/brand";

const fade: Variants = {
  hidden: { opacity: 0, y: 16 },
  show: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.08, duration: 0.5, ease: "easeOut" as const },
  }),
};

export function Hero() {
  return (
    <section className="relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 -z-10 opacity-[0.07] brand-gradient" />
      <div className="mx-auto max-w-6xl px-4 py-20 text-center md:py-28">
        <motion.span
          custom={0}
          variants={fade}
          initial="hidden"
          animate="show"
          className="inline-flex items-center gap-2 rounded-full border border-border bg-surface px-3 py-1 text-xs font-medium text-muted"
        >
          <span className="h-2 w-2 rounded-full bg-teal" />
          Now planning trips from {brand.defaultMarket.city}
        </motion.span>

        <motion.h1
          custom={1}
          variants={fade}
          initial="hidden"
          animate="show"
          className="mx-auto mt-6 max-w-3xl text-4xl font-bold tracking-tight text-foreground md:text-6xl"
        >
          Plan your whole trip with{" "}
          <span className="brand-text-gradient">one AI</span> — flights, hotels & documents.
        </motion.h1>

        <motion.p
          custom={2}
          variants={fade}
          initial="hidden"
          animate="show"
          className="mx-auto mt-6 max-w-2xl text-lg text-muted"
        >
          Enter a destination and {brand.name} assembles flights, hotels and a budget-aware
          itinerary — then verifies and fixes your travel documents with AI before you fly.
        </motion.p>

        <motion.div
          custom={3}
          variants={fade}
          initial="hidden"
          animate="show"
          className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row"
        >
          <Link
            href="/register"
            className="w-full rounded-xl brand-gradient px-6 py-3 text-base font-semibold text-white shadow-md transition hover:opacity-90 sm:w-auto"
          >
            Start planning free
          </Link>
          <a
            href="#features"
            className="w-full rounded-xl border border-border bg-surface px-6 py-3 text-base font-semibold text-foreground transition hover:bg-surface-muted sm:w-auto"
          >
            See features
          </a>
        </motion.div>
      </div>
    </section>
  );
}
