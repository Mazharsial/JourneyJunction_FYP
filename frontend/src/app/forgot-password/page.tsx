"use client";

import { useState } from "react";
import Link from "next/link";
import { AuthShell } from "@/components/AuthShell";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { authApi, ApiError } from "@/lib/api";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await authApi.requestPasswordReset(email);
      setDone(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Request failed. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthShell
      title="Reset your password"
      subtitle="Enter your email and we'll send reset instructions."
      footer={
        <Link href="/login" className="font-semibold text-brand-blue hover:underline">
          Back to sign in
        </Link>
      }
    >
      {done ? (
        <Alert tone="success">
          If an account exists for that email, a password reset link has been sent.
        </Alert>
      ) : (
        <form onSubmit={onSubmit} className="space-y-4" noValidate>
          {error && <Alert tone="error">{error}</Alert>}
          <Input
            label="Email"
            name="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
          />
          <Button type="submit" full loading={submitting}>
            Send reset link
          </Button>
        </form>
      )}
    </AuthShell>
  );
}
