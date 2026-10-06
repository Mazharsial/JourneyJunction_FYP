import { Navbar } from "@/components/Navbar";
import { Hero } from "@/components/Hero";
import { Features } from "@/components/Features";
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
            <div className="mt-14 grid gap-8 md:grid-cols-3">
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

        <section id="pricing" className="mx-auto max-w-6xl px-4 py-20 text-center">
          <h2 className="text-3xl font-bold tracking-tight text-foreground md:text-4xl">
            Start free. Upgrade when you need more AI.
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-muted">
            Core planning is free. Advanced document verification, personalised itineraries and
            priority support come with a subscription. Detailed plans arrive soon.
          </p>
        </section>
      </main>
      <Footer />
    </>
  );
}
