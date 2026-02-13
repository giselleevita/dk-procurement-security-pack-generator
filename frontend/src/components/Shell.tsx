import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import type { Me } from "../api/types";

export function Shell({
  me,
  onLoggedOut,
  children,
}: {
  me: Me;
  onLoggedOut: () => void;
  children: React.ReactNode;
}) {
  const nav = useNavigate();

  async function logout() {
    try {
      await api.post("/api/auth/logout");
    } finally {
      onLoggedOut();
      nav("/login");
    }
  }

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">
          <Link to="/">DK Security Pack</Link>
        </div>
        <nav className="nav">
          <Link to="/">Dashboard</Link>
          <Link to="/connections">Connect</Link>
          <button className="linkbtn" onClick={logout}>
            Logout
          </button>
        </nav>
        <div className="me">{me.email}</div>
      </header>
      <main className="main">{children}</main>
    </div>
  );
}

