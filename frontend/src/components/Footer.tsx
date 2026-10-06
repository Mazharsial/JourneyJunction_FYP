import { brand } from "@/lib/brand";

export function Footer() {
  return (
    <footer className="mt-auto border-t border-border bg-surface">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-4 py-8 text-sm text-muted md:flex-row">
        <p>
          © {new Date().getFullYear()} {brand.name}. Built as a Final Year Project.
        </p>
        <p className="text-xs">
          {brand.name} provides informational travel guidance, not legal or visa advice.
        </p>
      </div>
    </footer>
  );
}
