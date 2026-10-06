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
  amadeus: string;
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
};

export function isAdmin(roles: string[]): boolean {
  return roles.includes("admin") || roles.includes("super_admin");
}
