import Link from "next/link";
import { Navbar } from "@/components/Navbar";
import { Hero } from "@/components/Hero";
import { Features } from "@/components/Features";
import { PricingSection } from "@/components/PricingSection";
import { Footer } from "@/components/Footer";
import { brand } from "@/lib/brand";

const steps = [
  { n: "1", t: "Tell us where", d: "Enter your destination and travel dates." },
  { n: "2", t: "Get your plan", d: "Flights, hotels, budget and itinerary — assembled by AI." },
  { n: "3", t: "Verify documents", d: "Upload your docs; AI checks and fixes them before you fly." },
];

export default function Home() {
  return (
    <>
      <Navbar />
      <main className="flex-1">
        <Hero />
        <Features />

        <section id="how" className="border-y border-border bg-surface-muted/40">
          <div className="mx-auto max-w-6xl px-4 py-20">
            <h2 className="text-center text-3xl font-bold tracking-tight text-foreground md:text-4xl">
              How {brand.name} works
            </h2>
            <div className="mt-14 grid grid-cols-1 gap-8 md:grid-cols-3">
              {steps.map((s) => (
                <div key={s.n} className="text-center">
                  <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full brand-gradient text-lg font-bold text-white">
                    {s.n}
                  </div>
                  <h3 className="mt-4 text-lg font-semibold text-foreground">{s.t}</h3>
                  <p className="mt-2 text-sm text-muted">{s.d}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <PricingSection />

        <section className="border-t border-border bg-surface-muted/40">
          <div className="mx-auto max-w-4xl px-4 py-16 text-center">
            <h2 className="text-2xl font-bold text-foreground md:text-3xl">
              Ready to plan your trip?
            </h2>
            <p className="mx-auto mt-3 max-w-xl text-muted">
              Create a free account to open your dashboard — plan trips, chat with the AI assistant,
              verify documents and manage your subscription.
            </p>
            <div className="mt-6 flex flex-col items-center justify-center gap-3 sm:flex-row">
              <Link href="/register" className="w-full rounded-xl brand-gradient px-6 py-3 text-base font-semibold text-white shadow-md transition hover:opacity-90 sm:w-auto">
                Create free account
              </Link>
              <Link href="/login" className="w-full rounded-xl border border-border bg-surface px-6 py-3 text-base font-semibold text-foreground transition hover:bg-surface-muted sm:w-auto">
                Sign in
              </Link>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}
