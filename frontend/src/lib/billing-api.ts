/** Typed client for billing & subscriptions. */
import { apiFetch } from "@/lib/api";

export interface FeatureOut {
  feature_key: string;
  enabled: boolean;
  limit_value: number;
}
export interface PlanOut {
  code: string;
  name: string;
  description: string;
  price_cents: number;
  currency: string;
  interval: string;
  purchasable: boolean;
  features: FeatureOut[];
}
export interface PlansResponse {
  plans: PlanOut[];
  publishable_key: string;
  billing_enabled: boolean;
}
export interface SubscriptionOut {
  plan_code: string;
  plan_name: string;
  status: string;
  current_period_end: string | null;
  usage: { feature: string; enabled: boolean; limit: number; used: number }[];
}

export const billingApi = {
  plans: () => apiFetch<PlansResponse>("/billing/plans"),
  subscription: (token: string) => apiFetch<SubscriptionOut>("/billing/subscription", { token }),
  checkout: (token: string, plan_code: string) =>
    apiFetch<{ url: string }>("/billing/checkout", { method: "POST", token, body: { plan_code } }),
  portal: (token: string) => apiFetch<{ url: string }>("/billing/portal", { method: "POST", token }),
};

const FEATURE_LABELS: Record<string, string> = {
  trip_planning: "Trip planning",
  chatbot_messages: "AI assistant messages / month",
  ocr_documents: "Document checks / month",
  whatsapp: "WhatsApp assistant",
  priority_support: "Priority support",
};

export function featureLabel(key: string): string {
  return FEATURE_LABELS[key] ?? key;
}

export function featureValue(f: FeatureOut): string {
  if (!f.enabled || f.limit_value === 0) return "—";
  if (f.limit_value === -1) return "Unlimited";
  return String(f.limit_value);
}
