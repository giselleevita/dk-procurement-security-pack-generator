import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { api, ApiError } from "../api/client";
import type { Me } from "../api/types";

export function LoginPage({
  onAuthed,
  demoMode,
  demoEmail,
}: {
  onAuthed: (me: Me) => void;
  demoMode?: boolean;
  demoEmail?: string | null;
}) {
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setBusy(true);
    try {
      const me = await api.post<Me>("/api/auth/login", { email, password });
      onAuthed(me);
      nav("/");
    } catch (e2) {
      const msg = e2 instanceof ApiError ? JSON.stringify(e2.detail) : "Login failed";
      setErr(msg);
    } finally {
      setBusy(false);
    }
  }

  async function demoLogin() {
    setErr(null);
    setBusy(true);
    try {
      const me = await api.post<Me>("/api/auth/demo-login");
      onAuthed(me);
      nav("/");
    } catch (e2) {
      const msg = e2 instanceof ApiError ? JSON.stringify(e2.detail) : "Demo login failed";
      setErr(msg);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth">
      {/* ── Value proposition ──────────────────────── */}
      <div className="auth__hero">
        <h1>DK Security Pack</h1>
        <p className="auth__tagline">
          Generate a GDPR-ready procurement security pack in minutes. 18 automated controls,
          ISO 27001 & NIS2 mapped, PDF + DPA template included.
        </p>
        <div className="auth__features">
          <span className="auth__feat">✓ Local-only, no telemetry</span>
          <span className="auth__feat">✓ GitHub + Microsoft Entra</span>
          <span className="auth__feat">✓ PDF + DPA export</span>
          <span className="auth__feat">✓ Self-hosted</span>
        </div>
      </div>

      {/* ── Demo callout ───────────────────────────── */}
      {demoMode && (
        <div className="demo-callout card">
          <p className="demo-callout__title">🎬 Demo mode</p>
          <p className="muted">
            Pre-filled with sample data for <strong>CloudSec ApS</strong>. No setup required.
          </p>
          {demoEmail && (
            <p className="muted demo-callout__creds">
              Email: <code>{demoEmail}</code> · Password: <code>demo1234567</code>
            </p>
          )}
          <button className="btn-demo" onClick={demoLogin} disabled={busy} type="button">
            {busy ? "Signing in…" : "Try demo — one click"}
          </button>
          <div className="demo-callout__divider">or sign in manually below</div>
        </div>
      )}

      {/* ── Login form ─────────────────────────────── */}
      <form onSubmit={submit} className="card">
        <h2>Sign in</h2>
        <label>
          Email
          <input
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            type="email"
            autoComplete="email"
            required
          />
        </label>
        <label>
          Password
          <input
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            type="password"
            autoComplete="current-password"
            required
          />
        </label>
        {err ? <div className="error">{err}</div> : null}
        <button disabled={busy} type="submit">
          {busy ? "Signing in…" : "Sign in"}
        </button>
        <p className="muted">
          No account? <Link to="/register">Create one</Link>
        </p>
      </form>
    </div>
  );
}
