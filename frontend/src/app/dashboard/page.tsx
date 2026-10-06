"use client";

import { useAuth } from "@/lib/auth-context";
import { Alert } from "@/components/ui/Alert";

const tiles = [
  { title: "Plan a trip", body: "Enter a destination to get flights, hotels and an itinerary.", soon: true },
  { title: "My trips", body: "View and manage your saved trips.", soon: true },
  { title: "Verify documents", body: "Upload a passport or visa form for AI checks.", soon: true },
  { title: "AI assistant", body: "Ask about visas, routes and requirements.", soon: true },
];

export default function DashboardHome() {
  const { user } = useAuth();
  if (!user) return null;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">
          Welcome{user.full_name ? `, ${user.full_name}` : ""} 👋
        </h1>
        <p className="mt-1 text-sm text-muted">
          Role: <span className="font-medium text-foreground">{user.roles.join(", ") || "—"}</span>
        </p>
      </div>

      {!user.is_verified && (
        <Alert tone="info">
          Your email isn&apos;t verified yet. Verification will be enabled when email delivery is
          configured.
        </Alert>
      )}

      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {tiles.map((t) => (
          <div key={t.title} className="rounded-2xl border border-border bg-surface p-5">
            <h3 className="text-sm font-semibold text-foreground">{t.title}</h3>
            <p className="mt-2 text-xs leading-relaxed text-muted">{t.body}</p>
            {t.soon && (
              <span className="mt-3 inline-block rounded-full bg-surface-muted px-2.5 py-0.5 text-[11px] font-medium text-muted">
                Coming soon
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
