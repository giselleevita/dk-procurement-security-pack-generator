import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, ApiError } from "../api/client";
import type { ControlDetail } from "../api/types";

function statusClass(s: string) {
  if (s === "pass") return "pill pass";
  if (s === "warn") return "pill warn";
  if (s === "fail") return "pill fail";
  return "pill unknown";
}

export function ControlDetailPage() {
  const params = useParams();
  const key = params.key ? decodeURIComponent(params.key) : "";
  const [row, setRow] = useState<ControlDetail | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!key) return;
    let alive = true;
    api
      .get<ControlDetail>(`/api/controls/${encodeURIComponent(key)}`)
      .then((r) => {
        if (!alive) return;
        setRow(r);
        setErr(null);
      })
      .catch((e) => {
        if (!alive) return;
        setRow(null);
        setErr(e instanceof ApiError ? JSON.stringify(e.detail) : "Failed to load");
      });
    return () => {
      alive = false;
    };
  }, [key]);

  return (
    <div className="stack">
      <div className="card">
        <div className="rowHead">
          <div>
            <h1>Control</h1>
            <div className="muted">{key}</div>
          </div>
          <div>
            {row ? <span className={statusClass(row.status)}>{row.status}</span> : null}
          </div>
        </div>
        <div className="muted">
          <Link to="/">← Back to dashboard</Link>
        </div>
      </div>

      {err ? <div className="error">{err}</div> : null}

      {row ? (
        <>
          <section className="card">
            <h2>{row.title_en}</h2>
            <div className="muted" style={{ marginBottom: 4 }}>{row.title_dk}</div>
            {row.description_en && <p>{row.description_en}</p>}
            <div className="muted">Collected at: {row.collected_at ? row.collected_at : "—"}</div>
          </section>

          {/* Framework mapping */}
          {(row.iso27001_clauses.length > 0 || row.nis2_articles.length > 0) && (
            <section className="card">
              <h2>Compliance framework mapping</h2>
              {row.iso27001_clauses.length > 0 && (
                <div style={{ marginBottom: 8 }}>
                  <strong>ISO 27001:2022</strong>{" "}
                  <span className="muted">{row.iso27001_clauses.join(", ")}</span>
                </div>
              )}
              {row.nis2_articles.length > 0 && (
                <div>
                  <strong>NIS2 Directive</strong>{" "}
                  <span className="muted">{row.nis2_articles.join(", ")}</span>
                </div>
              )}
            </section>
          )}

          {/* Notes */}
          <section className="card">
            <h2>Evidence notes</h2>
            <pre className="pre">{row.notes}</pre>
          </section>

          {/* Remediation */}
          {(row.remediation_en || row.remediation_dk) && row.status !== "pass" && (
            <section className="card">
              <h2>How to fix</h2>
              {row.remediation_en && <p>{row.remediation_en}</p>}
              {row.remediation_dk && (
                <p className="muted" style={{ fontSize: "0.9em" }}>
                  {row.remediation_dk}
                </p>
              )}
            </section>
          )}

          {/* Raw artifacts */}
          <section className="card">
            <h2>Artifacts (JSON)</h2>
            <pre className="pre">{JSON.stringify(row.artifacts, null, 2)}</pre>
          </section>
        </>
      ) : (
        <div className="muted">Loading...</div>
      )}
    </div>
  );
}
