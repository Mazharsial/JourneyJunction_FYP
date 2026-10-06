"use client";

/**
 * Auth state for the SPA.
 *
 * Access token is held in memory; the refresh token is persisted in
 * localStorage so the session survives reloads (bootstrapped via /refresh on
 * mount). NOTE: localStorage is readable by JS — acceptable for this FYP with
 * CSP/headers in place; httpOnly-cookie sessions are a future hardening step.
 */
import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { authApi, ApiError, type UserOut } from "@/lib/api";

const REFRESH_KEY = "journeyjunction_refresh";

interface AuthState {
  user: UserOut | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<string | null | undefined>;
  logout: () => Promise<void>;
  /** Run an authenticated API call, auto-refreshing the access token once on 401. */
  authCall: <T>(fn: (token: string) => Promise<T>) => Promise<T>;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

function readRefresh(): string | null {
  try {
    return localStorage.getItem(REFRESH_KEY);
  } catch {
    return null;
  }
}
function writeRefresh(token: string | null) {
  try {
    if (token) localStorage.setItem(REFRESH_KEY, token);
    else localStorage.removeItem(REFRESH_KEY);
  } catch {
    /* storage unavailable */
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(null);
  const [loading, setLoading] = useState(true);
  const accessToken = useRef<string | null>(null);

  const applyTokens = useCallback(async (access: string, refresh: string) => {
    accessToken.current = access;
    writeRefresh(refresh);
    const me = await authApi.me(access);
    setUser(me);
  }, []);

  const bootstrap = useCallback(async () => {
    const refresh = readRefresh();
    if (!refresh) {
      setLoading(false);
      return;
    }
    try {
      const tokens = await authApi.refresh(refresh);
      await applyTokens(tokens.access_token, tokens.refresh_token);
    } catch {
      writeRefresh(null);
      accessToken.current = null;
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, [applyTokens]);

  useEffect(() => {
    void bootstrap();
  }, [bootstrap]);

  const login = useCallback(
    async (email: string, password: string) => {
      const tokens = await authApi.login(email, password);
      await applyTokens(tokens.access_token, tokens.refresh_token);
    },
    [applyTokens],
  );

  const register = useCallback(
    async (email: string, password: string, fullName: string) => {
      const res = await authApi.register(email, password, fullName);
      await applyTokens(res.tokens.access_token, res.tokens.refresh_token);
      return res.verification_token; // dev convenience (null in prod)
    },
    [applyTokens],
  );

  const authCall = useCallback(async <T,>(fn: (token: string) => Promise<T>): Promise<T> => {
    const run = async (token: string | null): Promise<T> => {
      if (!token) throw new ApiError("Not authenticated.", "not_authenticated", 401);
      return fn(token);
    };
    try {
      return await run(accessToken.current);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        const refresh = readRefresh();
        if (refresh) {
          const tokens = await authApi.refresh(refresh);
          accessToken.current = tokens.access_token;
          writeRefresh(tokens.refresh_token);
          return run(tokens.access_token);
        }
      }
      throw err;
    }
  }, []);

  const logout = useCallback(async () => {
    const refresh = readRefresh();
    if (refresh) {
      try {
        await authApi.logout(refresh);
      } catch {
        /* best-effort */
      }
    }
    writeRefresh(null);
    accessToken.current = null;
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, authCall }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within <AuthProvider>");
  return ctx;
}

export { ApiError };
