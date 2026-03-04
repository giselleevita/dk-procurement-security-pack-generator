import { useEffect, useState } from "react";
import { api, ApiError } from "../api/client";
import type { Connection } from "../api/types";
import { ProviderIcon } from "../components/ProviderIcon";
import { useToast } from "../context/ToastContext";

type Provider = "github" | "microsoft";

function ConnCard({
  provider,
  conn,
  onConnect,
  onForget,
  busy,
}: {
  provider: Provider;
  conn?: Connection;
  onConnect: () => void;
  onForget: () => void;
  busy: boolean;
}) {
  const [confirming, setConfirming] = useState(false);
  const label = provider === "github" ? "GitHub" : "Microsoft Entra / Graph";
  const desc =
    provider === "github"
      ? "Branch protection, PR review policies, force-push rules, repo visibility."
      : "Security defaults, Conditional Access policies, admin account surface area.";

  return (
    <div className={`conn-card${conn?.connected ? " conn-card--on" : ""}`}>
      <div className="conn-card__logo">
        <ProviderIcon provider={provider} size={26} />
      </div>
      <div className="conn-card__body">
        <div className="conn-card__name">{label}</div>
        <div className="conn-card__desc muted">{desc}</div>
        {conn?.connected && conn.scopes && (
          <div className="conn-card__meta muted">Scopes: {conn.scopes}</div>
        )}
        {conn?.connected && conn.expires_at && (
          <div className="conn-card__meta muted">Token expires: {conn.expires_at.slice(0, 10)}</div>
        )}
        {conn?.connected && conn.provider_account_id && (
          <div className="conn-card__meta muted">Account: {conn.provider_account_id}</div>
        )}
      </div>
      <div className="conn-card__actions">
        {conn?.connected ? (
          <>
            <span className="conn-status conn-status--on">● Connected</span>
            {confirming ? (
              <div className="conn-confirm">
                <span className="muted">Remove connection?</span>
                <div className="conn-confirm__btns">
                  <button
                    className="dangerBtn"
                    disabled={busy}
                    onClick={() => {
                      setConfirming(false);
                      onForget();
                    }}
                  >
                    Yes, remove
                  </button>
                  <button className="secondary" onClick={() => setConfirming(false)}>
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <button className="secondary" disabled={busy} onClick={() => setConfirming(true)}>
                Disconnect
              </button>
            )}
          </>
        ) : (
          <>
            <span className="conn-status conn-status--off">○ Not connected</span>
            <button disabled={busy} onClick={onConnect}>
              Connect →
            </button>
          </>
        )}
      </div>
    </div>
  );
}

export function ConnectionsPage() {
  const toast = useToast();
  const [rows, setRows] = useState<Connection[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [wipingConfirm, setWipingConfirm] = useState(false);

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
      toast.success(`${provider} connected successfully`);
    } else if (status === "error" && provider) {
      toast.error(`${provider} connection failed: ${msg ?? "unknown error"}`);
    }
    load();
  }, []);

  async function start(provider: Provider) {
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

  async function forget(provider: Provider) {
    setBusy(provider);
    setErr(null);
    try {
      await api.del(`/api/connections/${provider}`);
      await load();
      toast.success(`${provider} connection removed`);
    } catch (e) {
      setErr(e instanceof ApiError ? JSON.stringify(e.detail) : "Failed to remove connection");
      toast.error("Could not remove connection");
    } finally {
      setBusy(null);
    }
  }

  async function wipe() {
    setBusy("wipe");
    setErr(null);
    try {
      await api.post("/api/wipe");
      window.location.href = "/login";
    } catch (e) {
      setErr(e instanceof ApiError ? JSON.stringify(e.detail) : "Wipe failed");
      toast.error("Wipe failed");
    } finally {
      setBusy(null);
      setWipingConfirm(false);
    }
  }

  const github = rows.find((r) => r.provider === "github");
  const microsoft = rows.find((r) => r.provider === "microsoft");
  const connectedCount = [github, microsoft].filter((c) => c?.connected).length;

  return (
    <div className="stack">
      <section className="card">
        <h1>Connect accounts</h1>
        <p className="muted">
          OAuth tokens are stored encrypted in the local database. The app only calls GitHub and
          Microsoft Graph when you click "Collect now" — never in the background.
        </p>
        {connectedCount > 0 && (
          <div className="conn-summary">
            <span className="conn-status conn-status--on">
              ● {connectedCount} of 2 providers connected
            </span>
          </div>
        )}
      </section>

      {err ? <div className="error">{err}</div> : null}

      <section className="card conn-list">
        <ConnCard
          provider="microsoft"
          conn={microsoft}
          onConnect={() => start("microsoft")}
          onForget={() => forget("microsoft")}
          busy={busy !== null}
        />
        <ConnCard
          provider="github"
          conn={github}
          onConnect={() => start("github")}
          onForget={() => forget("github")}
          busy={busy !== null}
        />
      </section>

      <section className="card card--danger-zone">
        <h2>Danger zone</h2>
        <p className="muted">
          Wipe all data for this account — connections, evidence, attestations, and vendor profile.
          This cannot be undone.
        </p>
        {wipingConfirm ? (
          <div className="wipe-confirm">
            <p className="wipe-confirm__msg">
              ⚠ This will permanently delete all your data and log you out.
            </p>
            <div className="conn-confirm__btns">
              <button className="dangerBtn" disabled={busy !== null} onClick={wipe}>
                {busy === "wipe" ? "Wiping…" : "Yes, wipe everything"}
              </button>
              <button className="secondary" onClick={() => setWipingConfirm(false)}>
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <button
            className="dangerBtn"
            disabled={busy !== null}
            onClick={() => setWipingConfirm(true)}
          >
            Wipe all data
          </button>
        )}
      </section>
    </div>
  );
}
