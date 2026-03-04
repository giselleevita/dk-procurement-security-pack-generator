import { useEffect, useState } from "react";
import { api, ApiError } from "../api/client";
import type { Attestation, AttestationStatus, ControlSummary } from "../api/types";

function statusClass(s: string) {
  if (s === "pass") return "pill pass";
  if (s === "warn") return "pill warn";
  if (s === "fail") return "pill fail";
  return "pill unknown";
}

type AttForm = {
  status: AttestationStatus;
  notes: string;
  attested_by: string;
};

function AttestationCard({
  control,
  att,
  onSaved,
}: {
  control: ControlSummary;
  att: Attestation | undefined;
  onSaved: (updated: Attestation) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState<AttForm>({
    status: att?.status ?? "unknown",
    notes: att?.notes ?? "",
    attested_by: att?.attested_by ?? "",
  });
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setErr(null);
    try {
      const updated = await api.put<Attestation>(
        `/api/attestations/${encodeURIComponent(control.key)}`,
        form
      );
      onSaved(updated);
      setEditing(false);
    } catch (e) {
      setErr(e instanceof ApiError ? JSON.stringify(e.detail) : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="card" style={{ marginBottom: 12 }}>
      <div className="rowHead" style={{ marginBottom: 8 }}>
        <div>
          <strong>{control.title_en}</strong>
          <div className="muted" style={{ fontSize: "0.85em" }}>{control.title_dk}</div>
          {control.description_en && (
            <div className="muted" style={{ fontSize: "0.85em", marginTop: 4 }}>
              {control.description_en}
            </div>
          )}
        </div>
        <span className={statusClass(att?.status ?? "unknown")}>{att?.status ?? "unknown"}</span>
      </div>

      {att?.attested_by && (
        <div className="muted" style={{ fontSize: "0.85em", marginBottom: 6 }}>
          Attested by {att.attested_by}
          {att.attested_at ? ` · ${att.attested_at.slice(0, 10)}` : ""}
        </div>
      )}

      {!editing ? (
        <button className="secondary" onClick={() => setEditing(true)}>
          {att ? "Edit attestation" : "Attest now"}
        </button>
      ) : (
        <form className="stack" onSubmit={save} style={{ marginTop: 8 }}>
          {err && <div className="error">{err}</div>}
          <label>
            Status
            <select
              value={form.status}
              onChange={(e) => setForm((f) => ({ ...f, status: e.target.value as AttestationStatus }))}
            >
              <option value="pass">Pass — control is fully in place</option>
              <option value="warn">Warn — partially in place / planned</option>
              <option value="fail">Fail — not in place</option>
              <option value="unknown">Unknown — not assessed</option>
            </select>
          </label>
          <label>
            Notes (describe what is in place, dates, document references)
            <textarea
              value={form.notes}
              maxLength={2000}
              rows={4}
              onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
              placeholder="IR plan maintained in Confluence. Last tabletop exercise: 2025-11-01."
            />
          </label>
          <label>
            Attested by (name / title)
            <input
              type="text"
              value={form.attested_by}
              maxLength={255}
              onChange={(e) => setForm((f) => ({ ...f, attested_by: e.target.value }))}
              placeholder="Jane Jensen, CISO"
            />
          </label>
          <div className="actions">
            <button type="submit" disabled={saving}>
              {saving ? "Saving..." : "Save attestation"}
            </button>
            <button type="button" className="secondary" onClick={() => setEditing(false)}>
              Cancel
            </button>
          </div>
        </form>
      )}
    </div>
  );
}

export function AttestationsPage() {
  const [controls, setControls] = useState<ControlSummary[]>([]);
  const [atts, setAtts] = useState<Record<string, Attestation>>({});
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      api.get<ControlSummary[]>("/api/dashboard"),
      api.get<Attestation[]>("/api/attestations"),
    ])
      .then(([cs, as_]) => {
        setControls(cs.filter((c) => c.is_attestation));
        const byKey: Record<string, Attestation> = {};
        for (const a of as_) byKey[a.control_key] = a;
        setAtts(byKey);
      })
      .catch((e) => setErr(e instanceof ApiError ? JSON.stringify(e.detail) : "Failed to load"))
      .finally(() => setLoading(false));
  }, []);

  function onSaved(updated: Attestation) {
    setAtts((prev) => ({ ...prev, [updated.control_key]: updated }));
  }

  const total = controls.length;
  const attested = controls.filter(
    (c) => atts[c.key] && atts[c.key].status !== "unknown"
  ).length;

  return (
    <div className="stack">
      <section className="card">
        <h1>Manual attestations</h1>
        <p className="muted">
          These controls cannot be collected automatically. Self-certify each control, add notes
          describing what is in place, and name the person attesting. Attestations are included in
          every exported security pack.
        </p>
        <div className="summary">
          <span className="pill pass">Attested {attested}</span>
          <span className="pill unknown">Remaining {total - attested}</span>
        </div>
      </section>

      {err && <div className="error">{err}</div>}

      {loading ? (
        <div className="muted">Loading...</div>
      ) : (
        controls.map((c) => (
          <AttestationCard
            key={c.key}
            control={c}
            att={atts[c.key]}
            onSaved={onSaved}
          />
        ))
      )}
    </div>
  );
}
