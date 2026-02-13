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
          <Link to="/">Back to dashboard</Link>
        </div>
      </div>

      {err ? <div className="error">{err}</div> : null}

      {row ? (
        <>
          <section className="card">
            <h2>{row.title_dk}</h2>
            <div className="muted">{row.title_en}</div>
            <div className="muted">Collected at: {row.collected_at ? row.collected_at : "-"}</div>
          </section>

          <section className="card">
            <h2>Notes</h2>
            <pre className="pre">{row.notes}</pre>
          </section>

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
