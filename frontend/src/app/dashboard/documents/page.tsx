"use client";

import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Select } from "@/components/ui/Select";
import { Alert } from "@/components/ui/Alert";
import { useAuth } from "@/lib/auth-context";
import { ApiError } from "@/lib/api";
import {
  documentsApi,
  type AnalysisOut,
  type DocumentDetail,
  type DocumentOut,
  type Finding,
} from "@/lib/documents-api";

function FindingRow({ f }: { f: Finding }) {
  const color =
    f.severity === "error" ? "text-error" : f.severity === "warning" ? "text-warning" : "text-muted";
  const dot =
    f.severity === "error" ? "bg-error" : f.severity === "warning" ? "bg-warning" : "bg-muted";
  return (
    <li className="flex gap-3 rounded-xl border border-border bg-surface p-3">
      <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${dot}`} />
      <div>
        <p className={`text-sm font-medium ${color}`}>
          <span className="uppercase">{f.severity}</span> · {f.message}
        </p>
        {f.suggestion && <p className="mt-0.5 text-xs text-muted">Suggestion: {f.suggestion}</p>}
      </div>
    </li>
  );
}

function AnalysisView({ a }: { a: AnalysisOut }) {
  const errors = a.findings.filter((f) => f.severity === "error").length;
  return (
    <div className="space-y-5">
      <Alert tone={errors ? "error" : "success"}>
        {a.summary} <span className="opacity-70">(engine: {a.engine}, confidence {(a.overall_confidence * 100).toFixed(0)}%)</span>
      </Alert>

      {a.compliance && (a.compliance as { requirement?: string }).requirement && (
        <Alert tone="info">
          <strong className="capitalize">
            Visa: {String((a.compliance as { requirement: string }).requirement).replace(/_/g, " ")}
          </strong>{" "}
          {String((a.compliance as { notes?: string }).notes ?? "")}
          <span className="mt-1 block text-xs opacity-80">
            {String((a.compliance as { disclaimer?: string }).disclaimer ?? "")}
          </span>
        </Alert>
      )}

      <div>
        <h3 className="text-sm font-semibold text-foreground">Extracted fields</h3>
        <div className="mt-2 overflow-hidden rounded-xl border border-border">
          <table className="w-full text-sm">
            <tbody>
              {a.fields
                .filter((f) => f.raw_value || f.issue)
                .map((f) => (
                  <tr key={f.field_name} className="border-b border-border last:border-0">
                    <td className="bg-surface-muted px-3 py-2 font-medium capitalize text-muted">
                      {f.field_name.replace(/_/g, " ")}
                    </td>
                    <td className="px-3 py-2 text-foreground">{f.raw_value || "—"}</td>
                    <td className="px-3 py-2 text-xs text-error">{f.issue}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>

      {a.findings.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-foreground">Issues to review</h3>
          <ul className="mt-2 space-y-2">
            {a.findings.map((f, i) => (
              <FindingRow key={i} f={f} />
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default function DocumentsPage() {
  const { authCall } = useAuth();
  const [docType, setDocType] = useState("passport");
  const [consent, setConsent] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DocumentDetail | null>(null);
  const [docs, setDocs] = useState<DocumentOut[]>([]);
  const fileRef = useRef<HTMLInputElement>(null);

  async function refresh() {
    try {
      setDocs(await authCall((t) => documentsApi.list(t)));
    } catch {
      /* ignore */
    }
  }
  useEffect(() => {
    void refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function onUpload(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!file) return setError("Please choose a file (JPG, PNG or PDF).");
    if (!consent) return setError("Please give consent to process your document.");
    setUploading(true);
    setResult(null);
    try {
      const res = await authCall((t) => documentsApi.upload(t, file, docType, consent));
      setResult(res);
      setFile(null);
      if (fileRef.current) fileRef.current.value = "";
      setConsent(false);
      await refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed. Please try again.");
    } finally {
      setUploading(false);
    }
  }

  async function openDoc(id: string) {
    setError(null);
    try {
      setResult(await authCall((t) => documentsApi.get(t, id)));
    } catch {
      setError("Could not load that document.");
    }
  }

  async function del(id: string) {
    try {
      await authCall((t) => documentsApi.remove(t, id));
      if (result?.id === id) setResult(null);
      await refresh();
    } catch {
      setError("Could not delete that document.");
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Document verification</h1>
        <p className="mt-1 text-sm text-muted">
          Upload a passport, visa or ticket. AI extracts the details and checks for errors, missing
          fields and expiry before you travel.
        </p>
      </div>

      <form onSubmit={onUpload} className="space-y-4 rounded-2xl border border-border bg-surface p-6">
        {error && <Alert tone="error">{error}</Alert>}
        <div className="grid gap-4 sm:grid-cols-2">
          <Select
            label="Document type"
            value={docType}
            onChange={(e) => setDocType(e.target.value)}
            options={[
              { value: "passport", label: "Passport" },
              { value: "visa", label: "Visa" },
              { value: "ticket", label: "Ticket" },
              { value: "id", label: "ID card" },
              { value: "other", label: "Other" },
            ]}
          />
          <div className="space-y-1.5">
            <label htmlFor="file" className="block text-sm font-medium text-foreground">
              File (JPG, PNG, PDF · max 10 MB)
            </label>
            <input
              id="file"
              ref={fileRef}
              type="file"
              accept=".jpg,.jpeg,.png,.pdf,image/jpeg,image/png,application/pdf"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="w-full rounded-xl border border-border bg-surface px-3 py-2 text-sm file:mr-3 file:rounded-lg file:border-0 file:bg-surface-muted file:px-3 file:py-1.5 file:text-sm file:text-foreground"
            />
          </div>
        </div>
        <label className="flex items-start gap-2 text-xs text-muted">
          <input
            type="checkbox"
            checked={consent}
            onChange={(e) => setConsent(e.target.checked)}
            className="mt-0.5"
          />
          I consent to Journey Junction securely processing this document to verify it. It is encrypted and
          auto-deleted after the retention period.
        </label>
        <Button type="submit" loading={uploading}>
          {uploading ? "Analyzing…" : "Upload & verify"}
        </Button>
      </form>

      {result && result.analyses[0] && (
        <section className="rounded-2xl border border-border bg-surface p-6">
          <h2 className="mb-4 text-lg font-semibold text-foreground">
            Results — {result.display_name}
          </h2>
          <AnalysisView a={result.analyses[0]} />
        </section>
      )}

      <section>
        <h2 className="text-lg font-semibold text-foreground">Your documents</h2>
        {docs.length === 0 ? (
          <p className="mt-3 text-sm text-muted">No documents uploaded yet.</p>
        ) : (
          <div className="mt-3 space-y-2">
            {docs.map((d) => (
              <div key={d.id} className="flex items-center justify-between rounded-xl border border-border bg-surface p-3">
                <button onClick={() => openDoc(d.id)} className="text-left">
                  <p className="text-sm font-medium text-foreground">{d.display_name}</p>
                  <p className="text-xs text-muted capitalize">
                    {d.doc_type} · {d.status} · {new Date(d.created_at).toLocaleDateString()}
                  </p>
                </button>
                <button onClick={() => del(d.id)} className="text-xs font-medium text-error hover:underline">
                  Delete
                </button>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
