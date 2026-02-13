import { useEffect, useState } from "react";
import { api, ApiError } from "../api/client";
import type { Connection } from "../api/types";

export function ConnectionsPage() {
  const [rows, setRows] = useState<Connection[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  async function load() {
    setErr(null);
    try {
      const data = await api.get<Connection[]>("/api/connections");
      setRows(data);
    } catch (e) {
      setErr(e instanceof ApiError ? JSON.stringify(e.detail) : "Failed to load connections");
    }
  }

  useEffect(() => {
    const q = new URLSearchParams(window.location.search);
    const provider = q.get("provider");
    const status = q.get("status");
    const msg = q.get("error");
    if (status === "connected" && provider) {
      setNotice(`${provider} connected.`);
    } else if (status === "error" && provider) {
      setNotice(`${provider} connection failed: ${msg || "Unknown error"}`);
    }
    load();
  }, []);

  async function start(provider: "github" | "microsoft") {
    setBusy(provider);
    setErr(null);
    try {
      const res = await api.post<{ authorize_url: string }>(`/api/oauth/${provider}/start`);
      window.location.href = res.authorize_url;
    } catch (e) {
      setErr(e instanceof ApiError ? JSON.stringify(e.detail) : "Failed to start OAuth");
      setBusy(null);
    }
  }

  async function forget(provider: "github" | "microsoft") {
    if (!confirm(`Forget ${provider} connection? This deletes stored tokens.`)) return;
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

  async function wipe() {
    if (!confirm("Wipe all data for your user? This deletes evidence and connections.")) return;
    setBusy("wipe");
    setErr(null);
    try {
      await api.post("/api/wipe");
      await load();
    } catch (e) {
      setErr(e instanceof ApiError ? JSON.stringify(e.detail) : "Wipe failed");
    } finally {
      setBusy(null);
    }
  }

  const github = rows.find((r) => r.provider === "github");
  const microsoft = rows.find((r) => r.provider === "microsoft");

  return (
    <div className="stack">
      <section className="card">
        <h1>Connect accounts</h1>
        <p className="muted">
          Tokens are stored encrypted locally. The app calls GitHub and Microsoft Graph only when you collect evidence.
        </p>
      </section>

      {notice ? <div className="card">{notice}</div> : null}
      {err ? <div className="error">{err}</div> : null}

      <section className="card">
        <div className="provider">
          <div>
            <h2>GitHub</h2>
            <div className="muted">Scopes determine which evidence can be collected.</div>
          </div>
          <div className="right">
            <div className="muted">{github?.connected ? "Connected" : "Not connected"}</div>
            {github?.connected ? (
              <button className="secondary" disabled={busy !== null} onClick={() => forget("github")}>
                Forget
              </button>
            ) : (
              <button disabled={busy !== null} onClick={() => start("github")}>
                Connect
              </button>
            )}
          </div>
        </div>

        <div className="provider">
          <div>
            <h2>Microsoft (Entra / Graph)</h2>
            <div className="muted">Some endpoints require admin consent; unavailable evidence is marked Unknown.</div>
          </div>
          <div className="right">
            <div className="muted">{microsoft?.connected ? "Connected" : "Not connected"}</div>
            {microsoft?.connected ? (
              <button className="secondary" disabled={busy !== null} onClick={() => forget("microsoft")}>
                Forget
              </button>
            ) : (
              <button disabled={busy !== null} onClick={() => start("microsoft")}>
                Connect
              </button>
            )}
          </div>
        </div>
      </section>

      <section className="card danger">
        <h2>Safety actions</h2>
        <p className="muted">These actions only affect the current user in this local instance.</p>
        <button className="dangerBtn" disabled={busy !== null} onClick={wipe}>
          Wipe all data
        </button>
      </section>
    </div>
  );
}
