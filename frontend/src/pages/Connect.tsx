import { useEffect, useMemo, useState } from "react";
import { api, ApiError } from "../api/client";
import type { Connection } from "../api/types";

type Provider = "github" | "microsoft";

const providerOrder: Provider[] = ["github", "microsoft"];

export function ConnectPage() {
  const [rows, setRows] = useState<Connection[]>([]);
  const [busy, setBusy] = useState<Provider | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  async function load() {
    setErr(null);
    try {
      const data = await api.get<Connection[]>("/api/connections");
      setRows(data);
    } catch (e) {
      setErr(e instanceof ApiError ? JSON.stringify(e.detail) : "Failed to load provider connections");
    }
  }

  useEffect(() => {
    const q = new URLSearchParams(window.location.search);
    const provider = q.get("provider");
    const status = q.get("status");
    const msg = q.get("error");
    if (provider && status === "connected") {
      setNotice(`${provider} connected.`);
    }
    if (provider && status === "error") {
      setNotice(`${provider} connection failed: ${msg || "Unknown error"}`);
    }
    load();
  }, []);

  const progress = useMemo(() => {
    const connected = rows.filter((r) => r.connected).length;
    return { connected, total: 2, pct: Math.round((connected / 2) * 100) };
  }, [rows]);

  async function start(provider: Provider) {
    setBusy(provider);
    setErr(null);
    try {
      const res = await api.post<{ authorize_url: string }>(`/api/oauth/${provider}/start`);
      window.location.href = res.authorize_url;
    } catch (e) {
      setErr(e instanceof ApiError ? JSON.stringify(e.detail) : "Failed to start OAuth flow");
      setBusy(null);
    }
  }

  async function forget(provider: Provider) {
    if (!confirm(`Disconnect ${provider}?`)) return;
    setBusy(provider);
    setErr(null);
    try {
      await api.del(`/api/connections/${provider}`);
      await load();
    } catch (e) {
      setErr(e instanceof ApiError ? JSON.stringify(e.detail) : "Failed to forget provider");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="stack">
      <section className="card">
        <h1>Connection wizard</h1>
        <p className="muted">One-click onboarding for GitHub and Microsoft 365 evidence sources.</p>
        <div className="summary" style={{ marginTop: 10 }}>
          <span className="pill pass">Connected {progress.connected}/{progress.total}</span>
          <span className="pill unknown">Progress {progress.pct}%</span>
        </div>
      </section>

      {notice ? <div className="card">{notice}</div> : null}
      {err ? <div className="error">{err}</div> : null}

      <section className="card">
        {providerOrder.map((provider) => {
          const row = rows.find((r) => r.provider === provider);
          const connected = !!row?.connected;
          const title = provider === "github" ? "GitHub" : "Microsoft 365 (Entra/Graph)";
          const subtitle =
            provider === "github"
              ? "Repository and org posture evidence."
              : "Identity and tenant posture evidence.";
          return (
            <div key={provider} className="provider">
              <div>
                <h2>{title}</h2>
                <div className="muted">{subtitle}</div>
              </div>
              <div className="right">
                <span className={connected ? "pill pass" : "pill warn"}>{connected ? "Connected" : "Not connected"}</span>
                {connected ? (
                  <button className="secondary" disabled={busy !== null} onClick={() => forget(provider)}>
                    Disconnect
                  </button>
                ) : (
                  <button disabled={busy !== null} onClick={() => start(provider)}>
                    Connect now
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </section>
    </div>
  );
}
