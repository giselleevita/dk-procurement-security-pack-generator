import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api/client";
import type { ControlSummary } from "../api/types";
import { ExportButton } from "../components/ExportButton";

function statusClass(s: string) {
  if (s === "pass") return "pill pass";
  if (s === "warn") return "pill warn";
  if (s === "fail") return "pill fail";
  return "pill unknown";
}

export function PackPreviewPage() {
  const [controls, setControls] = useState<ControlSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    setErr(null);
    setLoading(true);
    try {
      const rows = await api.get<ControlSummary[]>("/api/dashboard");
      setControls(rows);
    } catch (e) {
      setErr(e instanceof ApiError ? JSON.stringify(e.detail) : "Failed to load dashboard controls");
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

  return (
    <div className="stack">
      <section className="hero card">
        <div>
          <h1>Security pack preview</h1>
          <p className="muted">Review control outcomes before delivering evidence to procurement stakeholders.</p>
        </div>
        <div className="actions">
          <ExportButton format="pdf" className="secondary" onError={setErr} />
          <ExportButton format="zip" onError={setErr} />
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
        <div className="rowHead">
          <h2 style={{ margin: 0 }}>Included controls</h2>
          <Link to="/">Back to dashboard</Link>
        </div>
        {loading ? (
          <div className="muted">Loading...</div>
        ) : (
          <div className="rows" style={{ marginTop: 12 }}>
            {controls.map((c) => (
              <div key={c.key} className="row" style={{ cursor: "default" }}>
                <div className="title">
                  <div className="dk">{c.title_dk}</div>
                  <div className="en muted">{c.title_en}</div>
                </div>
                <div>
                  <span className={statusClass(c.status)}>{c.status}</span>
                </div>
                <div className="muted">{c.collected_at || "-"}</div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
