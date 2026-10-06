import Image from "next/image";
import Link from "next/link";
import { brand } from "@/lib/brand";

export function AuthShell({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
}) {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-4 py-10">
      <div className="w-full max-w-md">
        <Link href="/" className="mb-8 flex justify-center" aria-label={brand.name}>
          <Image src={brand.logo} alt={brand.name} width={200} height={50} priority className="h-11 w-auto" />
        </Link>
        <div className="rounded-2xl border border-border bg-surface p-7 shadow-sm">
          <h1 className="text-xl font-bold text-foreground">{title}</h1>
          {subtitle && <p className="mt-1 text-sm text-muted">{subtitle}</p>}
          <div className="mt-6">{children}</div>
        </div>
        {footer && <div className="mt-5 text-center text-sm text-muted">{footer}</div>}
      </div>
    </main>
  );
}
