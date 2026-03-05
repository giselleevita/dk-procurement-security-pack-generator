import { useState, useCallback } from "react";
import { useNavigate, Link } from "react-router-dom";
import { api, ApiError } from "../api/client";
import type { Me } from "../api/types";

// ── Password strength helpers ────────────────────────────────────────────────
function pwChecks(pw: string) {
  return {
    length: pw.length >= 8,
    upper: /[A-Z]/.test(pw),
    digit: /\d/.test(pw),
  };
}

function pwStrength(pw: string): "empty" | "weak" | "medium" | "strong" {
  if (!pw) return "empty";
  const { length, upper, digit } = pwChecks(pw);
  const met = [length, upper, digit].filter(Boolean).length;
  if (met === 3) return "strong";
  if (met === 2) return "medium";
  return "weak";
}

function StrengthMeter({ password }: { password: string }) {
  const strength = pwStrength(password);
  if (strength === "empty") return null;
  const checks = pwChecks(password);
  return (
    <div className="pw-strength">
      <div className={`pw-strength__bar pw-strength__bar--${strength}`}>
        <div className="pw-strength__fill" />
      </div>
      <ul className="pw-strength__hints">
        <li className={checks.length ? "hint--ok" : "hint--bad"}>
          {checks.length ? "✓" : "✗"} At least 8 characters
        </li>
        <li className={checks.upper ? "hint--ok" : "hint--bad"}>
          {checks.upper ? "✓" : "✗"} One uppercase letter
        </li>
        <li className={checks.digit ? "hint--ok" : "hint--bad"}>
          {checks.digit ? "✓" : "✗"} One digit
        </li>
      </ul>
    </div>
  );
}

// ── Page ────────────────────────────────────────────────────────────────────
export function RegisterPage({ onAuthed }: { onAuthed: (me: Me) => void }) {
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const strength = pwStrength(password);

  function parseError(e: unknown): string {
    if (e instanceof ApiError) {
      if (typeof e.detail === "string") return e.detail;
      if (Array.isArray(e.detail)) {
        // Pydantic validation errors: [{msg: "...", loc: [...]}]
        return e.detail.map((d: { msg?: string }) => d.msg ?? String(d)).join(" · ");
      }
      return JSON.stringify(e.detail);
    }
    return "Registration failed";
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (strength !== "strong" && strength !== "medium") {
      setErr("Please choose a stronger password (8+ chars, 1 uppercase, 1 digit).");
      return;
    }
    setErr(null);
    setBusy(true);
    try {
      const me = await api.post<Me>("/api/auth/register", { email, password });
      onAuthed(me);
      nav("/");
    } catch (e2) {
      setErr(parseError(e2));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth">
      <div className="auth__hero">
        <h1>DK Security Pack</h1>
        <p className="auth__tagline">Create a local account to get started.</p>
      </div>
      <form onSubmit={submit} className="card">
        <h2>Create account</h2>
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
            autoComplete="new-password"
            required
          />
        </label>
        <StrengthMeter password={password} />
        {err ? <div className="error">{err}</div> : null}
        <button disabled={busy || strength === "weak"} type="submit">
          {busy ? "Creating account…" : "Create account"}
        </button>
        <p className="muted">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </form>
    </div>
  );
}
