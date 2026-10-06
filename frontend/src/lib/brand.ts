/**
 * Single source of truth for brand identity.
 * Change the name/logo/tagline here (or via NEXT_PUBLIC_* env) — never hardcode
 * the brand elsewhere in the UI.
 */
export const brand = {
  name: process.env.NEXT_PUBLIC_BRAND_NAME ?? "Journey Junction",
  tagline: "AI-powered smart travel planning & document verification",
  logo: "/brand/journeyjunction-logo.svg",
  mark: "/brand/journeyjunction-mark.svg",
  // Initial market (configurable; mirrors backend defaults).
  defaultMarket: {
    city: process.env.NEXT_PUBLIC_DEFAULT_CITY ?? "Dubai",
    country: process.env.NEXT_PUBLIC_DEFAULT_COUNTRY ?? "AE",
    currency: process.env.NEXT_PUBLIC_DEFAULT_CURRENCY ?? "AED",
  },
} as const;

export const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
