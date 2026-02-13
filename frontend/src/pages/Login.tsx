import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { api, ApiError } from "../api/client";
import type { Me } from "../api/types";

export function LoginPage({ onAuthed }: { onAuthed: (me: Me) => void }) {
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

  return (
    <div className="auth">
      <h1>DK Security Pack</h1>
      <p className="muted">Local-only procurement security documentation pack generator.</p>
      <form onSubmit={submit} className="card">
        <h2>Login</h2>
        <label>
          Email
          <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" autoComplete="email" required />
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
          {busy ? "Signing in..." : "Sign in"}
        </button>
        <p className="muted">
          No account? <Link to="/register">Create one</Link>
        </p>
      </form>
    </div>
  );
}

