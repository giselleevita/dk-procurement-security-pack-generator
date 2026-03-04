import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, ApiError } from "../api/client";
import type { ControlDetail } from "../api/types";
import { StatusBadge } from "../components/StatusBadge";
import { ProviderIcon, PROVIDER_LABELS } from "../components/ProviderIcon";
import { ArtifactView } from "../components/ArtifactView";
import { relTime } from "../utils/time";

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
      <div className="detail-back">
        <Link to="/" className="muted">
          ← Dashboard
        </Link>
      </div>

      {err ? <div className="error">{err}</div> : null}

      {!row && !err ? (
        <section className="card">
          <div className="skeleton-rows">
            {[1, 2, 3].map((i) => (
              <div key={i} className="skeleton-row" />
            ))}
          </div>
        </section>
      ) : null}

      {row ? (
        <>
          {/* ── Header ─────────────────────────────── */}
          <section className="card detail-header">
            <div className="detail-header__top">
              <div className="detail-header__provider">
                <ProviderIcon provider={row.provider} size={15} />
                <span className="muted">{PROVIDER_LABELS[row.provider] ?? row.provider}</span>
                <code className="detail-header__key muted">{row.key}</code>
              </div>
              <StatusBadge status={row.status} large />
            </div>
            <h1 className="detail-header__title">{row.title_en}</h1>
            <p className="muted detail-header__title-dk">{row.title_dk}</p>
            {row.description_en && <p className="detail-header__desc">{row.description_en}</p>}
            {row.collected_at && (
              <div className="muted detail-header__collected">
                Last collected: <strong>{relTime(row.collected_at)}</strong>
              </div>
            )}
          </section>

          {/* ── Compliance mapping ─────────────────── */}
          {(row.iso27001_clauses.length > 0 || row.nis2_articles.length > 0) && (
            <section className="card">
              <h2 className="section-title">📋 Compliance framework mapping</h2>
              <div className="framework-grid">
                {row.iso27001_clauses.length > 0 && (
                  <div className="framework-group">
                    <div className="framework-group__label muted">ISO 27001:2022</div>
                    <div className="framework-chips">
                      {row.iso27001_clauses.map((c) => (
                        <span key={c} className="framework-chip framework-chip--iso">
                          {c}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {row.nis2_articles.length > 0 && (
                  <div className="framework-group">
                    <div className="framework-group__label muted">NIS2 Directive</div>
                    <div className="framework-chips">
                      {row.nis2_articles.map((a) => (
                        <span key={a} className="framework-chip framework-chip--nis2">
                          {a}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </section>
          )}

          {/* ── Remediation ────────────────────────── */}
          {row.status !== "pass" && (row.remediation_en || row.remediation_dk) && (
            <section className="card card--remediation">
              <h2 className="section-title">🔧 How to fix this</h2>
              {row.remediation_en && <p className="remediation-text">{row.remediation_en}</p>}
              {row.remediation_dk && (
                <p className="muted remediation-dk">{row.remediation_dk}</p>
              )}
            </section>
          )}

          {/* ── Evidence notes ─────────────────────── */}
          {row.notes && (
            <section className="card">
              <h2 className="section-title">📝 Evidence notes</h2>
              <pre className="pre">{row.notes}</pre>
            </section>
          )}

          {/* ── Collected data ─────────────────────── */}
          <section className="card">
            <h2 className="section-title">🔍 Collected data</h2>
            <ArtifactView artifacts={row.artifacts as Record<string, unknown>} />
          </section>
        </>
      ) : null}
    </div>
  );
}
