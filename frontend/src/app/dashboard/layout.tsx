"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/Button";
import { brand } from "@/lib/brand";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, loading, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  if (loading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <span
          className="h-7 w-7 animate-spin rounded-full border-2 border-border border-t-teal"
          aria-label="Loading"
        />
      </div>
    );
  }

  async function onLogout() {
    await logout();
    router.replace("/login");
  }

  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-border bg-surface">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <Link href="/dashboard" aria-label={brand.name}>
            <Image src={brand.logo} alt={brand.name} width={150} height={38} className="h-8 w-auto" priority />
          </Link>
          <div className="flex items-center gap-4">
            <span className="hidden text-sm text-muted sm:inline">
              {user.full_name || user.email}
            </span>
            <Button variant="secondary" onClick={onLogout} className="px-4 py-2">
              Sign out
            </Button>
          </div>
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">{children}</main>
    </div>
  );
}
