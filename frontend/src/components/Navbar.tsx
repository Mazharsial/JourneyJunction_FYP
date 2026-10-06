"use client";

import Image from "next/image";
import Link from "next/link";
import { useState } from "react";
import { brand } from "@/lib/brand";
import { useAuth } from "@/lib/auth-context";

type Item = { label: string; desc: string; href: string; icon: string };

const MENUS: { label: string; items: Item[]; promo?: { title: string; desc: string; href: string } }[] = [
  {
    label: "Product",
    items: [
      { label: "Trip Planner", desc: "Flights, hotels & itinerary in one place", href: "/register", icon: "🧭" },
      { label: "AI Assistant", desc: "Grounded answers on visas & routes", href: "/register", icon: "🤖" },
      { label: "Document Verification", desc: "OCR checks passports & visas", href: "/register", icon: "🛡️" },
      { label: "Travel Requirements", desc: "Visa types, fees & step-by-step prep", href: "/register", icon: "✅" },
    ],
  },
  {
    label: "Solutions",
    items: [
      { label: "Tourism", desc: "Plan leisure trips to the UAE & beyond", href: "/register", icon: "🏖️" },
      { label: "Umrah", desc: "Nusuk visa, vaccinations & Makkah hotels", href: "/register", icon: "🕋" },
      { label: "Hajj", desc: "Quota visas, packages & preparation", href: "/register", icon: "🧕" },
      { label: "Business travel", desc: "Fast itineraries and document checks", href: "/register", icon: "💼" },
    ],
  },
  {
    label: "Resources",
    items: [
      { label: "Guides", desc: "Visa & travel preparation playbooks", href: "/#how", icon: "📘" },
      { label: "Help Center", desc: "Get answers and support", href: "/#features", icon: "💬" },
      { label: "Changelog", desc: "See what's new", href: "/#features", icon: "⚡" },
    ],
    promo: { title: "See it in action", desc: "Create a free account and plan a trip in minutes.", href: "/register" },
  },
  {
    label: "Company",
    items: [
      { label: "About", desc: "Our mission for smarter travel", href: "/#features", icon: "🌍" },
      { label: "Pricing", desc: "Simple, transparent plans", href: "/#pricing", icon: "💳" },
      { label: "Contact", desc: "Talk to the team", href: "/register", icon: "✉️" },
    ],
  },
];

function Dropdown({ menu }: { menu: (typeof MENUS)[number] }) {
  return (
    <div className="group relative">
      <button className="flex items-center gap-1 py-2 text-sm font-medium text-muted transition hover:text-foreground">
        {menu.label}
        <svg className="h-4 w-4 transition group-hover:rotate-180" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.17l3.71-3.94a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clipRule="evenodd" />
        </svg>
      </button>
      <div className="invisible absolute left-1/2 top-full z-50 -translate-x-1/2 pt-3 opacity-0 transition-all duration-150 group-hover:visible group-hover:opacity-100">
        <div className="w-[min(92vw,34rem)] rounded-2xl border border-border bg-surface p-3 shadow-xl">
          <div className={`grid gap-1 ${menu.promo ? "sm:grid-cols-2" : ""}`}>
            <div className="space-y-1">
              {menu.items.map((it) => (
                <Link key={it.label} href={it.href} className="flex items-start gap-3 rounded-xl p-2.5 transition hover:bg-surface-muted">
                  <span className="text-xl">{it.icon}</span>
                  <span>
                    <span className="block text-sm font-semibold text-foreground">{it.label}</span>
                    <span className="block text-xs text-muted">{it.desc}</span>
                  </span>
                </Link>
              ))}
            </div>
            {menu.promo && (
              <Link href={menu.promo.href} className="flex flex-col justify-between rounded-xl brand-gradient p-4 text-white">
                <span>
                  <span className="block text-sm font-bold">{menu.promo.title}</span>
                  <span className="mt-1 block text-xs opacity-90">{menu.promo.desc}</span>
                </span>
                <span className="mt-4 text-xs font-semibold">Get started →</span>
              </Link>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export function Navbar() {
  const { user, loading } = useAuth();
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-surface/80 backdrop-blur">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link href="/" className="flex items-center" aria-label={brand.name}>
          <Image src={brand.logo} alt={brand.name} width={168} height={42} priority className="h-9 w-auto" />
        </Link>

        <div className="hidden items-center gap-6 lg:flex">
          {MENUS.map((m) => <Dropdown key={m.label} menu={m} />)}
          <Link href="/#pricing" className="py-2 text-sm font-medium text-muted transition hover:text-foreground">Pricing</Link>
        </div>

        <div className="flex items-center gap-3">
          {!loading && user ? (
            <Link href="/dashboard" className="rounded-lg brand-gradient px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:opacity-90">
              Go to dashboard
            </Link>
          ) : (
            <>
              <Link href="/login" className="hidden rounded-lg px-4 py-2 text-sm font-medium text-foreground hover:bg-surface-muted sm:inline-block">
                Log in
              </Link>
              <Link href="/register" className="rounded-lg brand-gradient px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:opacity-90">
                Start planning free
              </Link>
            </>
          )}
          <button
            onClick={() => setOpen((v) => !v)}
            aria-label="Menu"
            className="rounded-lg border border-border p-2 text-foreground lg:hidden"
          >
            <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path d="M3 5h14M3 10h14M3 15h14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /></svg>
          </button>
        </div>
      </nav>

      {open && (
        <div className="border-t border-border bg-surface px-4 py-3 lg:hidden">
          {MENUS.flatMap((m) => m.items).slice(0, 8).map((it) => (
            <Link key={it.label} href={it.href} onClick={() => setOpen(false)} className="flex items-center gap-3 rounded-lg px-2 py-2 text-sm text-foreground hover:bg-surface-muted">
              <span>{it.icon}</span> {it.label}
            </Link>
          ))}
          <Link href="/#pricing" onClick={() => setOpen(false)} className="flex items-center gap-3 rounded-lg px-2 py-2 text-sm text-foreground hover:bg-surface-muted">💳 Pricing</Link>
        </div>
      )}
    </header>
  );
}
