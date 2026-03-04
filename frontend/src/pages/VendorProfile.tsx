import { useEffect, useState } from "react";
import { api, ApiError } from "../api/client";
import type { VendorProfile } from "../api/types";

const EMPTY: VendorProfile = {
  company_name: "",
  cvr_number: "",
  address: "",
  contact_name: "",
  contact_email: "",
  contact_phone: "",
  security_officer_name: "",
  security_officer_title: "",
  pack_scope: "",
  pack_recipient: "",
  pack_validity_months: 6,
};

export function VendorProfilePage() {
  const [form, setForm] = useState<VendorProfile>(EMPTY);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<VendorProfile>("/api/vendor-profile")
      .then((v) => setForm(v))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  function set(field: keyof VendorProfile, value: string | number) {
    setSaved(false);
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setErr(null);
    setSaved(false);
    try {
      const updated = await api.put<VendorProfile>("/api/vendor-profile", form);
      setForm(updated);
      setSaved(true);
    } catch (e) {
      setErr(e instanceof ApiError ? JSON.stringify(e.detail) : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <div className="muted">Loading...</div>;

  return (
    <div className="stack">
      <section className="card">
        <h1>Vendor profile</h1>
        <p className="muted">
          This information appears on the cover page and signature block of every exported security
          pack. Fill it in before your first export.
        </p>
      </section>

      {err && <div className="error">{err}</div>}
      {saved && <div className="success">Saved.</div>}

      <form className="card stack" onSubmit={save}>
        <fieldset>
          <legend>Danish company registry</legend>

          <label>
            Company legal name (as registered on virk.dk)
            <input
              type="text"
              value={form.company_name}
              maxLength={255}
              onChange={(e) => set("company_name", e.target.value)}
              placeholder="Acme ApS"
            />
          </label>

          <label>
            CVR number (8 digits)
            <input
              type="text"
              value={form.cvr_number}
              maxLength={8}
              pattern="\d{0,8}"
              onChange={(e) => set("cvr_number", e.target.value.replace(/\D/g, ""))}
              placeholder="12345678"
            />
          </label>

          <label>
            Registered address
            <input
              type="text"
              value={form.address}
              maxLength={500}
              onChange={(e) => set("address", e.target.value)}
              placeholder="Strandvejen 1, 2900 Hellerup, Danmark"
            />
          </label>
        </fieldset>

        <fieldset>
          <legend>Contact person</legend>

          <label>
            Name
            <input
              type="text"
              value={form.contact_name}
              maxLength={255}
              onChange={(e) => set("contact_name", e.target.value)}
              placeholder="Jane Jensen"
            />
          </label>

          <label>
            Email
            <input
              type="email"
              value={form.contact_email}
              maxLength={320}
              onChange={(e) => set("contact_email", e.target.value)}
              placeholder="jane@acme.dk"
            />
          </label>

          <label>
            Phone
            <input
              type="text"
              value={form.contact_phone}
              maxLength={50}
              onChange={(e) => set("contact_phone", e.target.value)}
              placeholder="+45 20 30 40 50"
            />
          </label>
        </fieldset>

        <fieldset>
          <legend>Signing authority</legend>
          <p className="muted" style={{ fontSize: "0.9em", marginTop: 0 }}>
            This person's name and title appear in the declaration block on the pack PDF.
          </p>

          <label>
            Name
            <input
              type="text"
              value={form.security_officer_name}
              maxLength={255}
              onChange={(e) => set("security_officer_name", e.target.value)}
              placeholder="John Doe"
            />
          </label>

          <label>
            Title
            <input
              type="text"
              value={form.security_officer_title}
              maxLength={255}
              onChange={(e) => set("security_officer_title", e.target.value)}
              placeholder="Chief Information Security Officer"
            />
          </label>
        </fieldset>

        <fieldset>
          <legend>Pack context</legend>

          <label>
            Scope — which product(s) / system(s) does this pack cover?
            <textarea
              value={form.pack_scope}
              maxLength={1000}
              rows={3}
              onChange={(e) => set("pack_scope", e.target.value)}
              placeholder="SaaS platform 'Acme Procurement Tool' — all production environments."
            />
          </label>

          <label>
            Recipient (optional — who is this pack prepared for?)
            <input
              type="text"
              value={form.pack_recipient}
              maxLength={500}
              onChange={(e) => set("pack_recipient", e.target.value)}
              placeholder="Region Midtjylland — udbud ref. 2026-XYZ"
            />
          </label>

          <label>
            Pack validity (months)
            <input
              type="number"
              value={form.pack_validity_months}
              min={1}
              max={60}
              onChange={(e) => set("pack_validity_months", parseInt(e.target.value) || 6)}
            />
          </label>
        </fieldset>

        <div className="actions">
          <button type="submit" disabled={saving}>
            {saving ? "Saving..." : "Save profile"}
          </button>
        </div>
      </form>
    </div>
  );
}
