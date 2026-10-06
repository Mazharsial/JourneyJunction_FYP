import Image from "next/image";
import Link from "next/link";
import { brand } from "@/lib/brand";

export function Navbar() {
  return (
    <header className="sticky top-0 z-50 border-b border-border bg-surface/80 backdrop-blur">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link href="/" className="flex items-center" aria-label={brand.name}>
          <Image
            src={brand.logo}
            alt={brand.name}
            width={168}
            height={42}
            priority
            className="h-9 w-auto"
          />
        </Link>
        <div className="hidden items-center gap-8 text-sm font-medium text-muted md:flex">
          <a href="#features" className="hover:text-foreground">Features</a>
          <a href="#how" className="hover:text-foreground">How it works</a>
          <a href="#pricing" className="hover:text-foreground">Pricing</a>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/login"
            className="hidden rounded-lg px-4 py-2 text-sm font-medium text-foreground hover:bg-surface-muted sm:inline-block"
          >
            Sign in
          </Link>
          <Link
            href="/register"
            className="rounded-lg brand-gradient px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:opacity-90"
          >
            Get started
          </Link>
        </div>
      </nav>
    </header>
  );
}
