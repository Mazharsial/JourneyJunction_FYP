"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState } from "react";

/** Auto-cycling, animated preview of the app's core flows. Self-contained. */
const SCENES = ["plan", "assistant", "documents", "requirements"] as const;
type Scene = (typeof SCENES)[number];

const TABS: Record<Scene, string> = {
  plan: "Plan a trip",
  assistant: "AI assistant",
  documents: "Verify documents",
  requirements: "Travel requirements",
};

function PlanScene() {
  const rows = [
    { a: "Emirates", r: "LHE → DXB", p: "AED 1,968" },
    { a: "Qatar Airways", r: "LHE → DXB", p: "AED 1,990" },
    { a: "flydubai", r: "LHE → DXB", p: "AED 2,003" },
  ];
  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <div className="flex-1 rounded-lg bg-surface-muted px-3 py-2 text-xs text-muted">Dubai (DXB) · AE</div>
        <div className="rounded-lg brand-gradient px-3 py-2 text-xs font-semibold text-white">Plan</div>
      </div>
      {rows.map((r, i) => (
        <motion.div
          key={r.a}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.15 + i * 0.18 }}
          className="flex items-center justify-between rounded-lg border border-border bg-surface px-3 py-2"
        >
          <span className="text-xs font-medium text-foreground">{r.a}</span>
          <span className="text-[10px] text-muted">{r.r}</span>
          <span className="text-xs font-bold text-brand-blue">{r.p}</span>
        </motion.div>
      ))}
    </div>
  );
}

function AssistantScene() {
  const full = "Yes — Pakistani travellers need a UAE tourist visa (up to 30 days). Apply before you fly.";
  const [typed, setTyped] = useState("");
  useEffect(() => {
    setTyped("");
    let i = 0;
    const id = setInterval(() => {
      i += 2;
      setTyped(full.slice(0, i));
      if (i >= full.length) clearInterval(id);
    }, 28);
    return () => clearInterval(id);
  }, []);
  return (
    <div className="space-y-2">
      <div className="ml-auto w-fit rounded-2xl brand-gradient px-3 py-2 text-xs text-white">
        Do I need a visa for Dubai from Pakistan?
      </div>
      <div className="w-[90%] rounded-2xl border border-border bg-surface px-3 py-2 text-xs text-foreground">
        {typed}
        <span className="ml-0.5 inline-block h-3 w-0.5 animate-pulse bg-foreground align-middle" />
      </div>
      <div className="flex flex-wrap gap-1.5">
        {["Visa cost?", "Documents?", "Hotels in Dubai"].map((c) => (
          <span key={c} className="rounded-full border border-border bg-surface px-2 py-0.5 text-[10px] text-muted">{c}</span>
        ))}
      </div>
    </div>
  );
}

function DocumentsScene() {
  const fields = [
    { k: "Full name", v: "KHAN, AHMED", ok: true },
    { k: "Passport no.", v: "AB1234567", ok: true },
    { k: "Expiry date", v: "2024-01-21", ok: false },
  ];
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 rounded-lg bg-surface-muted px-3 py-2">
        <span className="text-lg">🛡️</span>
        <span className="text-xs font-medium text-foreground">passport.png</span>
        <span className="ml-auto rounded-full bg-teal/10 px-2 py-0.5 text-[10px] font-semibold text-teal">gemini-vision · 100%</span>
      </div>
      {fields.map((f, i) => (
        <motion.div
          key={f.k}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 + i * 0.2 }}
          className="flex items-center justify-between rounded-lg border border-border bg-surface px-3 py-1.5"
        >
          <span className="text-[10px] text-muted">{f.k}</span>
          <span className={`text-xs font-medium ${f.ok ? "text-foreground" : "text-warning"}`}>
            {f.v} {f.ok ? "✓" : "⚠"}
          </span>
        </motion.div>
      ))}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.9 }}
        className="rounded-lg border border-warning/40 bg-warning/5 px-3 py-2 text-[10px] text-warning"
      >
        ERROR · Document expired — renew before travelling.
      </motion.div>
    </div>
  );
}

function RequirementsScene() {
  const steps = [
    { t: "Meningococcal (ACWY) vaccine", s: "Mandatory" },
    { t: "Umrah visa via Nusuk", s: "SAR 300+" },
    { t: "Return ticket + hotel", s: "Required" },
  ];
  return (
    <div className="space-y-2">
      <div className="rounded-lg bg-surface-muted px-3 py-2 text-xs font-semibold text-foreground">
        Travel requirements · <span className="text-ai">UMRAH</span>
      </div>
      {steps.map((r, i) => (
        <motion.div
          key={r.t}
          initial={{ opacity: 0, x: -12 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.15 + i * 0.18 }}
          className="flex items-center gap-2 rounded-lg border border-border bg-surface px-3 py-2"
        >
          <span className="flex h-5 w-5 items-center justify-center rounded-full brand-gradient text-[10px] font-bold text-white">{i + 1}</span>
          <span className="text-xs text-foreground">{r.t}</span>
          <span className="ml-auto text-[10px] text-muted">{r.s}</span>
        </motion.div>
      ))}
    </div>
  );
}

const SCENE_EL: Record<Scene, React.ReactNode> = {
  plan: <PlanScene />,
  assistant: <AssistantScene />,
  documents: <DocumentsScene />,
  requirements: <RequirementsScene />,
};

export function HeroDemo() {
  const [idx, setIdx] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setIdx((v) => (v + 1) % SCENES.length), 3800);
    return () => clearInterval(id);
  }, []);
  const scene = SCENES[idx];

  return (
    <div className="relative">
      <div className="pointer-events-none absolute -inset-6 -z-10 rounded-[2rem] brand-gradient opacity-20 blur-2xl" />
      <div className="overflow-hidden rounded-2xl border border-border bg-surface shadow-2xl">
        {/* browser chrome */}
        <div className="flex items-center gap-2 border-b border-border bg-surface-muted px-4 py-2.5">
          <span className="h-2.5 w-2.5 rounded-full bg-error/70" />
          <span className="h-2.5 w-2.5 rounded-full bg-warning/70" />
          <span className="h-2.5 w-2.5 rounded-full bg-success/70" />
          <span className="ml-3 truncate rounded-md bg-surface px-3 py-0.5 text-[10px] text-muted">
            journeyjunction.app/dashboard
          </span>
        </div>
        {/* tabs */}
        <div className="flex gap-1 overflow-x-auto border-b border-border px-3 py-2">
          {SCENES.map((s) => (
            <span
              key={s}
              className={`whitespace-nowrap rounded-full px-2.5 py-1 text-[10px] font-medium transition ${
                s === scene ? "brand-gradient text-white" : "text-muted"
              }`}
            >
              {TABS[s]}
            </span>
          ))}
        </div>
        {/* scene */}
        <div className="h-[260px] p-4">
          <AnimatePresence mode="wait">
            <motion.div
              key={scene}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.35 }}
            >
              {SCENE_EL[scene]}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
      <p className="mt-3 text-center text-xs text-muted">Live preview — flights, AI answers, document checks & requirements.</p>
    </div>
  );
}
