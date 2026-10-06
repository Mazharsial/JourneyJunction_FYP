"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { AuthShell } from "@/components/AuthShell";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { authApi, ApiError } from "@/lib/api";

function ResetForm() {
  const router = useRouter();
  const params = useSearchParams();
  const [token, setToken] = useState(params.get("token") ?? "");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [fieldError, setFieldError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setFieldError(null);
    if (password.length < 8) {
      setFieldError("Password must be at least 8 characters.");
      return;
    }
    setSubmitting(true);
    try {
      await authApi.confirmPasswordReset(token, password);
      setDone(true);
      setTimeout(() => router.push("/login"), 1500);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Reset failed. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  if (done) {
    return <Alert tone="success">Password updated. Redirecting to sign in…</Alert>;
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4" noValidate>
      {error && <Alert tone="error">{error}</Alert>}
      <Input
        label="Reset token"
        name="token"
        required
        value={token}
        onChange={(e) => setToken(e.target.value)}
        placeholder="Paste the token from your email"
      />
      <Input
        label="New password"
        name="new_password"
        type="password"
        autoComplete="new-password"
        required
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="At least 8 characters"
        error={fieldError ?? undefined}
      />
      <Button type="submit" full loading={submitting}>
        Update password
      </Button>
    </form>
  );
}

export default function ResetPasswordPage() {
  return (
    <AuthShell
      title="Choose a new password"
      footer={
        <Link href="/login" className="font-semibold text-brand-blue hover:underline">
          Back to sign in
        </Link>
      }
    >
      <Suspense fallback={<p className="text-sm text-muted">Loading…</p>}>
        <ResetForm />
      </Suspense>
    </AuthShell>
  );
}
