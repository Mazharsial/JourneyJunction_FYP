/** Typed client for notifications & preferences. */
import { apiFetch } from "@/lib/api";

export interface Preferences {
  full_name: string;
  phone_number: string;
  whatsapp_opt_in: boolean;
  email_opt_in: boolean;
  whatsapp_enabled: boolean;
  email_enabled: boolean;
}
export interface NotificationOut {
  id: string;
  channel: string;
  event: string;
  recipient: string;
  body: string;
  provider: string;
  status: string;
  created_at: string;
}

export const notificationsApi = {
  preferences: (t: string) => apiFetch<Preferences>("/notifications/preferences", { token: t }),
  updatePreferences: (t: string, patch: Partial<Preferences>) =>
    apiFetch<Preferences>("/notifications/preferences", { method: "PATCH", token: t, body: patch }),
  list: (t: string) => apiFetch<NotificationOut[]>("/notifications", { token: t }),
  test: (t: string, channel: "whatsapp" | "email", message: string) =>
    apiFetch<{ status: string; provider: string }>("/notifications/test", {
      method: "POST", token: t, body: { channel, message },
    }),
};
