import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api/client";
import type { CollectResponse, ControlSummary } from "../api/types";

function statusClass(s: string) {
  if (s === "pass") return "pill pass";
  if (s === "warn") return "pill warn";
  if (s === "fail") return "pill fail";
  return "pill unknown";
}

export function DashboardPage() {
  const [controls, setControls] = useState<ControlSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    setErr(null);
    setLoading(true);
    try {
      const rows = await api.get<ControlSummary[]>("/api/dashboard");
      setControls(rows);
    } catch (e) {
      setErr(e instanceof ApiError ? JSON.stringify(e.detail) : "Failed to load");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const counts = useMemo(() => {
    const c: Record<ControlSummary["status"], number> = { pass: 0, warn: 0, fail: 0, unknown: 0 };
    for (const x of controls) c[x.status] += 1;
    return c;
  }, [controls]);

  async function collectNow() {
    setBusy(true);
    setErr(null);
    try {
      await api.post<CollectResponse>("/api/collect");
      await load();
    } catch (e) {
      setErr(e instanceof ApiError ? JSON.stringify(e.detail) : "Collect failed");
    } finally {
      setBusy(false);
    }
  }

  async function exportPack() {
    setBusy(true);
    setErr(null);
    try {
      await api.download("/api/export", "dk-security-pack.zip");
    } catch (e) {
      setErr(e instanceof ApiError ? JSON.stringify(e.detail) : "Export failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="stack">
      <section className="hero card">
        <div>
          <h1>Dashboard</h1>
          <p className="muted">
            12 procurement-friendly controls. Deterministic, evidence-backed, local-only.
          </p>
        </div>
        <div className="actions">
          <button disabled={busy} onClick={collectNow}>
            {busy ? "Working..." : "Collect now"}
          </button>
          <button disabled={busy} onClick={exportPack} className="secondary">
            Export pack (ZIP)
          </button>
        </div>
        <div className="summary">
          <span className="pill pass">Pass {counts.pass}</span>
          <span className="pill warn">Warn {counts.warn}</span>
          <span className="pill fail">Fail {counts.fail}</span>
          <span className="pill unknown">Unknown {counts.unknown}</span>
        </div>
      </section>

      {err ? <div className="error">{err}</div> : null}

      <section className="card">
        <div className="tableHead">
          <div>Control</div>
          <div>Status</div>
          <div>Updated</div>
        </div>
        {loading ? (
          <div className="muted">Loading...</div>
        ) : (
          <div className="rows">
            {controls.map((c) => (
              <Link key={c.key} to={`/controls/${encodeURIComponent(c.key)}`} className="row">
                <div className="title">
                  <div className="dk">{c.title_dk}</div>
                  <div className="en muted">{c.title_en}</div>
                </div>
                <div>
                  <span className={statusClass(c.status)}>{c.status}</span>
                </div>
                <div className="muted">{c.collected_at ? c.collected_at : "-"}</div>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
