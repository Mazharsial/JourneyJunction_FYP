"use client";

import { type ButtonHTMLAttributes } from "react";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary";
  loading?: boolean;
  full?: boolean;
}

export function Button({
  variant = "primary",
  loading = false,
  full = false,
  className = "",
  children,
  disabled,
  ...rest
}: Props) {
  const base =
    "inline-flex items-center justify-center gap-2 rounded-xl px-5 py-2.5 text-sm font-semibold transition focus:outline-none focus-visible:ring-2 focus-visible:ring-teal focus-visible:ring-offset-2 disabled:opacity-60 disabled:cursor-not-allowed";
  const variants = {
    primary: "brand-gradient text-white shadow-sm hover:opacity-90",
    secondary: "border border-border bg-surface text-foreground hover:bg-surface-muted",
  };
  return (
    <button
      className={`${base} ${variants[variant]} ${full ? "w-full" : ""} ${className}`}
      disabled={disabled || loading}
      {...rest}
    >
      {loading && (
        <span
          className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white"
          aria-hidden
        />
      )}
      {children}
    </button>
  );
}
