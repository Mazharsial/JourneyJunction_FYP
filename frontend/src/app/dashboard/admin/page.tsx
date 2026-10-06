"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { useAuth } from "@/lib/auth-context";
import {
  adminApi,
  isAdmin,
  type AdminStats,
  type AdminUser,
  type AuditLog,
  type Health,
} from "@/lib/admin-api";
import { PlansManager } from "@/components/admin/PlansManager";
import { VisaRulesManager } from "@/components/admin/VisaRulesManager";

function StatCard({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-2xl border border-border bg-surface p-5">
      <p className="text-xs text-muted">{label}</p>
      <p className="mt-1 text-2xl font-bold text-foreground">{value}</p>
    </div>
  );
}

export default function AdminPage() {
  const { user, loading, authCall } = useAuth();
  const router = useRouter();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [health, setHealth] = useState<Health | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [q, setQ] = useState("");
  const [error, setError] = useState<string | null>(null);

  const admin = !!user && isAdmin(user.roles);

  useEffect(() => {
    if (!loading && user && !admin) router.replace("/dashboard");
  }, [loading, user, admin, router]);

  const loadUsers = useCallback(
    async (query = "") => {
      try {
        setUsers((await authCall((t) => adminApi.users(t, query))).items);
      } catch {
        setError("Could not load users.");
      }
    },
    [authCall],
  );

  useEffect(() => {
    if (!admin) return;
    authCall((t) => adminApi.stats(t)).then(setStats).catch(() => {});
    authCall((t) => adminApi.health(t)).then(setHealth).catch(() => {});
    authCall((t) => adminApi.auditLogs(t)).then((r) => setLogs(r.items)).catch(() => {});
    void loadUsers();
  }, [admin, authCall, loadUsers]);

  if (loading || !user) return <p className="text-sm text-muted">Loading…</p>;
  if (!admin) return null;

  async function toggleActive(u: AdminUser) {
    try {
      await authCall((t) => adminApi.updateUser(t, u.id, { is_active: !u.is_active }));
      await loadUsers(q);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Update failed.");
    }
  }

  async function toggleVerified(u: AdminUser) {
    try {
      await authCall((t) => adminApi.updateUser(t, u.id, { is_verified: !u.is_verified }));
      await loadUsers(q);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Update failed.");
    }
  }

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-foreground">Admin</h1>
      {error && <Alert tone="error">{error}</Alert>}

      {stats && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <StatCard label="Users" value={stats.users_total} />
          <StatCard label="Active users" value={stats.users_active} />
          <StatCard label="Trips" value={stats.trips_total} />
          <StatCard label="Documents" value={stats.documents_total} />
          <StatCard label="AI requests" value={stats.ai_requests_total} />
        </div>
      )}

      {health && (
        <div className="flex flex-wrap gap-2 text-xs">
          {Object.entries(health).map(([k, v]) => (
            <span key={k} className="rounded-full border border-border bg-surface px-3 py-1">
              <span className="capitalize text-muted">{k}: </span>
              <span className={v === "ok" || v === "configured" ? "text-success" : "text-muted"}>{v}</span>
            </span>
          ))}
        </div>
      )}

      <section>
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-lg font-semibold text-foreground">Users</h2>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              void loadUsers(q);
            }}
            className="flex gap-2"
          >
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search email/name"
              className="rounded-lg border border-border bg-surface px-3 py-1.5 text-sm outline-none focus:border-teal"
            />
            <Button type="submit" variant="secondary" className="px-3 py-1.5">Search</Button>
          </form>
        </div>
        <div className="mt-3 overflow-x-auto rounded-xl border border-border">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-surface-muted text-left text-xs text-muted">
                <th className="px-3 py-2">Email</th>
                <th className="px-3 py-2">Roles</th>
                <th className="px-3 py-2">Verified</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-t border-border">
                  <td className="px-3 py-2 text-foreground">{u.email}</td>
                  <td className="px-3 py-2 text-muted">{u.roles.join(", ")}</td>
                  <td className="px-3 py-2">
                    <button onClick={() => toggleVerified(u)} className="text-xs font-medium hover:underline">
                      <span className={u.is_verified ? "text-success" : "text-muted"}>
                        {u.is_verified ? "✓ verified" : "unverified"}
                      </span>
                    </button>
                  </td>
                  <td className="px-3 py-2">
                    <span className={u.is_active ? "text-success" : "text-error"}>
                      {u.is_active ? "active" : "disabled"}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-right">
                    <button onClick={() => toggleActive(u)} className="text-xs font-medium text-brand-blue hover:underline">
                      {u.is_active ? "Disable" : "Enable"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <PlansManager />

      <VisaRulesManager />

      <section>
        <h2 className="text-lg font-semibold text-foreground">Recent audit log</h2>
        <div className="mt-3 space-y-1">
          {logs.length === 0 && <p className="text-sm text-muted">No admin actions yet.</p>}
          {logs.slice(0, 15).map((l) => (
            <div key={l.id} className="flex justify-between rounded-lg border border-border bg-surface px-3 py-2 text-xs">
              <span className="font-medium text-foreground">{l.action}</span>
              <span className="text-muted">{l.entity} {l.entity_id} · {new Date(l.created_at).toLocaleString()}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
