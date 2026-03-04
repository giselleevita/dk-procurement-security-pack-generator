import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api/client";
import type { CollectResponse, ControlSummary } from "../api/types";
import { ScoreRing } from "../components/ScoreRing";
import { StatusBadge } from "../components/StatusBadge";
import { ProviderIcon, PROVIDER_LABELS, type ProviderKey } from "../components/ProviderIcon";
import { useToast } from "../context/ToastContext";
import { relTime } from "../utils/time";

const PROVIDER_ORDER: ProviderKey[] = ["microsoft", "github", "pack", "attestation"];

function SkeletonRows() {
  return (
    <div className="skeleton-rows">
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="skeleton-row" />
      ))}
    </div>
  );
}

export function DashboardPage() {
  const toast = useToast();
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

  const grouped = useMemo(() => {
    const g = new Map<string, ControlSummary[]>();
    for (const p of PROVIDER_ORDER) g.set(p, []);
    for (const c of controls) {
      if (!g.has(c.provider)) g.set(c.provider, []);
      g.get(c.provider)!.push(c);
    }
    return g;
  }, [controls]);

  const needsWork = useMemo(
    () =>
      controls
        .filter((c) => c.status === "fail" || c.status === "warn")
        .sort((a, b) => {
          if (a.status === "fail" && b.status !== "fail") return -1;
          if (b.status === "fail" && a.status !== "fail") return 1;
          return 0;
        }),
    [controls]
  );

  const noEvidence = !loading && controls.length > 0 && controls.every((c) => !c.collected_at);

  async function collectNow() {
    setBusy(true);
    setErr(null);
    try {
      const res = await api.post<CollectResponse>("/api/collect");
      await load();
      if (res.errors?.length) {
        toast.warn(`Collected with ${res.errors.length} error(s)`);
      } else {
        toast.success("Evidence collected successfully");
      }
    } catch (e) {
      const msg = e instanceof ApiError ? JSON.stringify(e.detail) : "Collect failed";
      setErr(msg);
      toast.error("Collection failed");
    } finally {
      setBusy(false);
    }
  }

  async function exportPack() {
    setBusy(true);
    setErr(null);
    try {
      await api.download("/api/export", "dk-security-pack.zip");
      toast.success("Pack exported — check your downloads");
    } catch (e) {
      const msg = e instanceof ApiError ? JSON.stringify(e.detail) : "Export failed";
      setErr(msg);
      toast.error("Export failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="stack">
      {/* ── Hero ─────────────────────────────────── */}
      <section className="card dash-hero">
        <ScoreRing
          pass={counts.pass}
          warn={counts.warn}
          fail={counts.fail}
          total={controls.length || 18}
        />
        <div className="dash-hero__body">
          <h1 className="dash-hero__title">Security Pack</h1>
          <div className="dash-hero__counts">
            <span className="dc-badge dc-badge--pass">✓ {counts.pass} pass</span>
            {counts.warn > 0 && <span className="dc-badge dc-badge--warn">⚠ {counts.warn} warn</span>}
            {counts.fail > 0 && <span className="dc-badge dc-badge--fail">✗ {counts.fail} fail</span>}
            {counts.unknown > 0 && (
              <span className="dc-badge dc-badge--unk">– {counts.unknown} unknown</span>
            )}
          </div>
          <div className="actions">
            <button disabled={busy} onClick={collectNow}>
              {busy ? "Working…" : "⟳  Collect now"}
            </button>
            <button disabled={busy} onClick={exportPack} className="secondary">
              ↓  Export pack (ZIP)
            </button>
          </div>
        </div>
      </section>

      {err ? <div className="error">{err}</div> : null}

      {/* ── Empty state ───────────────────────────── */}
      {noEvidence && (
        <section className="card empty-state">
          <div className="empty-state__icon">📡</div>
          <h2>No evidence collected yet</h2>
          <p className="muted">
            Connect GitHub and Microsoft, then click "Collect now" to pull live evidence across all{" "}
            {controls.length} controls.
          </p>
          <Link to="/connections" className="btn-inline">
            → Set up connections
          </Link>
        </section>
      )}

      {/* ── Needs attention ───────────────────────── */}
      {needsWork.length > 0 && (
        <section className="card">
          <h2 className="section-title">
            ⚡ Needs attention
            <span className="section-count">{needsWork.length}</span>
          </h2>
          <div className="rows">
            {needsWork.map((c) => (
              <Link
                key={c.key}
                to={`/controls/${encodeURIComponent(c.key)}`}
                className={`row row--alert row--alert-${c.status}`}
              >
                <div className="title">
                  <div className="dk">{c.title_en}</div>
                  <div className="en muted">{c.title_dk}</div>
                </div>
                <div>
                  <StatusBadge status={c.status} />
                </div>
                <div className="muted row__time">{relTime(c.collected_at)}</div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* ── Controls by provider ──────────────────── */}
      {loading ? (
        <section className="card">
          <SkeletonRows />
        </section>
      ) : (
        Array.from(grouped.entries()).map(([provider, pControls]) =>
          pControls.length === 0 ? null : (
            <section key={provider} className="card">
              <div className="provider-header">
                <span className="provider-header__icon">
                  <ProviderIcon provider={provider} size={17} />
                </span>
                <h2 className="provider-header__name">{PROVIDER_LABELS[provider] ?? provider}</h2>
                <span className="provider-header__count muted">{pControls.length} controls</span>
                <span className="provider-header__score">
                  {pControls.filter((c) => c.status === "pass").length}/{pControls.length} passing
                </span>
              </div>
              <div className="rows">
                {pControls.map((c) => (
                  <Link
                    key={c.key}
                    to={`/controls/${encodeURIComponent(c.key)}`}
                    className="row"
                  >
                    <div className="title">
                      <div className="dk">{c.title_en}</div>
                      <div className="en muted">{c.title_dk}</div>
                    </div>
                    <div>
                      <StatusBadge status={c.status} />
                    </div>
                    <div className="muted row__time">{relTime(c.collected_at)}</div>
                  </Link>
                ))}
              </div>
            </section>
          )
        )
      )}
    </div>
  );
}
