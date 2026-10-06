/** Typed client for the admin panel. */
import { apiFetch } from "@/lib/api";

export interface AdminStats {
  users_total: number;
  users_active: number;
  trips_total: number;
  documents_total: number;
  ai_requests_total: number;
  paid_subscriptions: Record<string, number>;
}
export interface Health {
  database: string;
  gemini: string;
  stripe: string;
  flights: string;
  hotels: string;
  whatsapp: string;
  email: string;
}
export interface AdminPlanFeature {
  feature_key: string;
  enabled: boolean;
  limit_value: number | null;
}
export interface AdminPlan {
  code: string;
  name: string;
  description: string;
  price_cents: number;
  currency: string;
  interval: string;
  purchasable: boolean;
  features: AdminPlanFeature[];
}
export interface VisaRule {
  id: string;
  origin_iso2: string;
  destination_iso2: string;
  requirement: string;
  allowed_stay_days: number | null;
  notes: string;
  source: string;
}
export interface VisaRuleInput {
  origin: string;
  destination: string;
  requirement: string;
  allowed_stay_days?: number | null;
  notes?: string;
  source?: string;
}
export interface AdminUser {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  roles: string[];
}
export interface UsersPage {
  items: AdminUser[];
  total: number;
  limit: number;
  offset: number;
}
export interface AuditLog {
  id: string;
  actor_user_id: string | null;
  action: string;
  entity: string;
  entity_id: string;
  meta: Record<string, unknown>;
  ip: string;
  created_at: string;
}

export const adminApi = {
  stats: (t: string) => apiFetch<AdminStats>("/admin/stats", { token: t }),
  health: (t: string) => apiFetch<Health>("/admin/health", { token: t }),
  users: (t: string, q = "") =>
    apiFetch<UsersPage>(`/admin/users${q ? `?q=${encodeURIComponent(q)}` : ""}`, { token: t }),
  updateUser: (t: string, id: string, patch: Partial<Pick<AdminUser, "is_active" | "is_verified" | "roles">>) =>
    apiFetch<AdminUser>(`/admin/users/${id}`, { method: "PATCH", token: t, body: patch }),
  auditLogs: (t: string) => apiFetch<{ items: AuditLog[]; total: number }>("/admin/audit-logs", { token: t }),

  plans: (t: string) => apiFetch<AdminPlan[]>("/admin/plans", { token: t }),
  updatePlanFeature: (
    t: string,
    code: string,
    body: { feature_key: string; enabled?: boolean | null; limit_value?: number | null },
  ) => apiFetch<AdminPlan>(`/admin/plans/${code}/features`, { method: "PATCH", token: t, body }),

  visaRules: (t: string) => apiFetch<VisaRule[]>("/admin/visa-rules", { token: t }),
  upsertVisaRule: (t: string, body: VisaRuleInput) =>
    apiFetch<VisaRule>("/admin/visa-rules", { method: "PUT", token: t, body }),
  deleteVisaRule: (t: string, id: string) =>
    apiFetch<null>(`/admin/visa-rules/${id}`, { method: "DELETE", token: t }),
};

export function isAdmin(roles: string[]): boolean {
  return roles.includes("admin") || roles.includes("super_admin");
}
