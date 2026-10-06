/**
 * Typed client for the Journey Junction API.
 *
 * Parses the backend's structured error envelope and throws `ApiError` with a
 * user-friendly message and machine-readable code.
 */
import { apiBaseUrl } from "@/lib/brand";

export interface UserOut {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_verified: boolean;
  roles: string[];
  permissions: string[];
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface RegisterResult {
  user: UserOut;
  tokens: TokenPair;
  verification_token?: string | null;
}

export class ApiError extends Error {
  code: string;
  status: number;
  constructor(message: string, code: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
  }
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  token?: string | null;
}

export async function apiFetch<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (opts.token) headers["Authorization"] = `Bearer ${opts.token}`;

  let resp: Response;
  try {
    resp = await fetch(`${apiBaseUrl}${path}`, {
      method: opts.method ?? "GET",
      headers,
      body: opts.body ? JSON.stringify(opts.body) : undefined,
    });
  } catch {
    throw new ApiError("Cannot reach the server. Please try again.", "network_error", 0);
  }

  let data: unknown = null;
  const text = await resp.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      /* non-JSON response */
    }
  }

  if (!resp.ok) {
    const envelope = data as { error?: { message?: string; code?: string } } | null;
    const message = envelope?.error?.message ?? "Something went wrong. Please try again.";
    const code = envelope?.error?.code ?? "error";
    throw new ApiError(message, code, resp.status);
  }
  return data as T;
}

// ---- auth endpoints ----
export const authApi = {
  register: (email: string, password: string, full_name: string) =>
    apiFetch<RegisterResult>("/auth/register", {
      method: "POST",
      body: { email, password, full_name },
    }),

  login: (email: string, password: string) =>
    apiFetch<TokenPair>("/auth/login", { method: "POST", body: { email, password } }),

  refresh: (refresh_token: string) =>
    apiFetch<TokenPair>("/auth/refresh", { method: "POST", body: { refresh_token } }),

  logout: (refresh_token: string) =>
    apiFetch<{ message: string }>("/auth/logout", { method: "POST", body: { refresh_token } }),

  me: (token: string) => apiFetch<UserOut>("/auth/me", { token }),

  verifyEmail: (token: string) =>
    apiFetch<{ message: string }>("/auth/verify-email", { method: "POST", body: { token } }),

  requestPasswordReset: (email: string) =>
    apiFetch<{ message: string }>("/auth/password-reset/request", {
      method: "POST",
      body: { email },
    }),

  confirmPasswordReset: (token: string, new_password: string) =>
    apiFetch<{ message: string }>("/auth/password-reset/confirm", {
      method: "POST",
      body: { token, new_password },
    }),
};
