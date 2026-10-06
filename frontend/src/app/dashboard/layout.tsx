"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/Button";
import { brand } from "@/lib/brand";
import { isAdmin } from "@/lib/admin-api";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: "🏠" },
  { href: "/dashboard/plan", label: "Plan a trip", icon: "🧭" },
  { href: "/dashboard/trips", label: "My trips", icon: "🧳" },
  { href: "/dashboard/assistant", label: "AI assistant", icon: "🤖" },
  { href: "/dashboard/documents", label: "Verify documents", icon: "🛡️" },
  { href: "/dashboard/billing", label: "Subscription", icon: "💳" },
  { href: "/dashboard/settings", label: "Settings", icon: "⚙️" },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, loading, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  useEffect(() => {
    setOpen(false); // close mobile drawer on route change
  }, [pathname]);

  if (loading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <span className="h-7 w-7 animate-spin rounded-full border-2 border-border border-t-teal" aria-label="Loading" />
      </div>
    );
  }

  const nav = [...NAV];
  if (isAdmin(user.roles)) nav.push({ href: "/dashboard/admin", label: "Admin", icon: "🛠️" });

  async function onLogout() {
    await logout();
    router.replace("/login");
  }

  function isActive(href: string) {
    return href === "/dashboard" ? pathname === href : pathname.startsWith(href);
  }

  const SidebarInner = (
    <div className="flex h-full flex-col">
      <Link href="/dashboard" aria-label={brand.name} className="flex items-center px-5 py-4">
        <Image src={brand.logo} alt={brand.name} width={150} height={38} className="h-8 w-auto" priority />
      </Link>
      <nav className="flex-1 space-y-1 px-3 py-2">
        {nav.map((n) => (
          <Link
            key={n.href}
            href={n.href}
            className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
              isActive(n.href)
                ? "brand-gradient text-white shadow-sm"
                : "text-muted hover:bg-surface-muted hover:text-foreground"
            }`}
          >
            <span className="text-base">{n.icon}</span>
            {n.label}
          </Link>
        ))}
      </nav>
      <div className="border-t border-border p-3">
        <div className="rounded-xl bg-surface-muted p-3">
          <p className="truncate text-sm font-semibold text-foreground">{user.full_name || "Traveller"}</p>
          <p className="truncate text-xs text-muted">{user.email}</p>
          <Button variant="secondary" onClick={onLogout} className="mt-3 w-full justify-center px-3 py-1.5 text-xs">
            Sign out
          </Button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-surface-muted/40">
      {/* desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-border bg-surface lg:block">
        {SidebarInner}
      </aside>

      {/* mobile drawer */}
      {open && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-black/40" onClick={() => setOpen(false)} />
          <aside className="absolute inset-y-0 left-0 w-64 border-r border-border bg-surface">{SidebarInner}</aside>
        </div>
      )}

      <div className="lg:pl-64">
        {/* top bar */}
        <header className="sticky top-0 z-30 flex items-center justify-between border-b border-border bg-surface/80 px-4 py-3 backdrop-blur">
          <button
            onClick={() => setOpen(true)}
            aria-label="Open menu"
            className="rounded-lg border border-border p-2 text-foreground lg:hidden"
          >
            <svg className="h-5 w-5" viewBox="0 0 20 20" fill="none"><path d="M3 5h14M3 10h14M3 15h14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /></svg>
          </button>
          <span className="hidden text-sm text-muted lg:block">
            Welcome back, <span className="font-semibold text-foreground">{user.full_name || "Traveller"}</span>
          </span>
          <div className="flex items-center gap-3">
            <Link href="/dashboard/plan" className="rounded-lg brand-gradient px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:opacity-90">
              + New trip
            </Link>
          </div>
        </header>

        <main className="mx-auto w-full max-w-6xl px-4 py-8">{children}</main>
      </div>
    </div>
  );
}
