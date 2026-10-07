"use client";

import { motion, type Variants } from "framer-motion";
import Link from "next/link";
import { brand } from "@/lib/brand";
import { HeroDemo } from "@/components/HeroDemo";

const fade: Variants = {
  hidden: { opacity: 0, y: 16 },
  show: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.08, duration: 0.5, ease: "easeOut" as const },
  }),
};

const bullets = [
  "Your first plan is free",
  "Flights, hotels & documents",
  "Tourism, Umrah & Hajj ready",
];

export function Hero() {
  return (
    <section className="relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 -z-10 opacity-[0.06] brand-gradient" />
      <div className="mx-auto grid max-w-6xl grid-cols-1 items-center gap-10 px-4 py-12 sm:py-16 md:py-24 lg:grid-cols-2">
        {/* left */}
        <div className="min-w-0">
          <motion.span
            custom={0}
            variants={fade}
            initial="hidden"
            animate="show"
            className="inline-flex items-center gap-2 rounded-full border border-teal/30 bg-teal/5 px-3 py-1 text-xs font-medium text-teal"
          >
            <span className="h-2 w-2 rounded-full bg-teal" />
            AI-powered travel planning & document verification
          </motion.span>

          <motion.h1
            custom={1}
            variants={fade}
            initial="hidden"
            animate="show"
            className="mt-5 max-w-xl text-3xl font-bold leading-[1.1] tracking-tight text-foreground sm:text-4xl md:text-5xl lg:text-6xl"
          >
            Your AI Travel Agent for{" "}
            <span className="brand-text-gradient">Dubai, Umrah & Hajj</span>
          </motion.h1>

          <motion.p
            custom={2}
            variants={fade}
            initial="hidden"
            animate="show"
            className="mt-5 max-w-xl text-lg text-muted"
          >
            Enter a destination and {brand.name} assembles flights, hotels and a budget-aware
            itinerary — answers your visa questions, verifies your documents with AI, and walks you
            through every requirement, step by step.
          </motion.p>

          <motion.div
            custom={3}
            variants={fade}
            initial="hidden"
            animate="show"
            className="mt-8 flex flex-col gap-3 sm:flex-row"
          >
            <Link
              href="/register"
              className="group inline-flex items-center justify-center gap-2 rounded-xl brand-gradient px-6 py-3 text-base font-semibold text-white shadow-md transition hover:opacity-90"
            >
              Start planning free
              <span className="transition group-hover:translate-x-1">→</span>
            </Link>
            <a
              href="#how"
              className="inline-flex items-center justify-center rounded-xl border border-border bg-surface px-6 py-3 text-base font-semibold text-foreground transition hover:bg-surface-muted"
            >
              See how it works
            </a>
          </motion.div>

          <motion.ul
            custom={4}
            variants={fade}
            initial="hidden"
            animate="show"
            className="mt-7 grid gap-2 text-sm text-muted sm:grid-cols-2"
          >
            {bullets.map((b) => (
              <li key={b} className="flex items-center gap-2">
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-teal/10 text-xs text-teal">✓</span>
                {b}
              </li>
            ))}
          </motion.ul>
        </div>

        {/* right: animated demo */}
        <motion.div
          initial={{ opacity: 0, scale: 0.96, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ delay: 0.25, duration: 0.6, ease: "easeOut" }}
          className="min-w-0"
        >
          <HeroDemo />
        </motion.div>
      </div>
    </section>
  );
}
