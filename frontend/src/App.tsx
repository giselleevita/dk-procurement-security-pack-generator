import { useEffect, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { useMe } from "./hooks/useMe";
import { api } from "./api/client";
import type { Me, Health } from "./api/types";
import { LoginPage } from "./pages/Login";
import { RegisterPage } from "./pages/Register";
import { DashboardPage } from "./pages/Dashboard";
import { ConnectionsPage } from "./pages/Connections";
import { ControlDetailPage } from "./pages/ControlDetail";
import { VendorProfilePage } from "./pages/VendorProfile";
import { AttestationsPage } from "./pages/Attestations";
import { Shell } from "./components/Shell";

export default function App() {
  const { me, setMe, loading } = useMe();
  const [demoMode, setDemoMode] = useState(false);
  const [demoEmail, setDemoEmail] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<Health>("/api/health")
      .then((h) => {
        setDemoMode(h.demo_mode);
        setDemoEmail(h.demo_email);
      })
      .catch(() => {
        // health check failure is non-fatal
      });
  }, []);

  function onAuthed(u: Me) {
    setMe(u);
  }

  function onLoggedOut() {
    setMe(null);
  }

  if (loading) return <div className="boot">Loading...</div>;

  return (
    <BrowserRouter>
      {me ? (
        <Shell me={me} onLoggedOut={onLoggedOut} demoMode={demoMode}>
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/connections" element={<ConnectionsPage />} />
            <Route path="/controls/:key" element={<ControlDetailPage />} />
            <Route path="/vendor-profile" element={<VendorProfilePage />} />
            <Route path="/attestations" element={<AttestationsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Shell>
      ) : (
        <Routes>
          <Route
            path="/login"
            element={<LoginPage onAuthed={onAuthed} demoMode={demoMode} demoEmail={demoEmail} />}
          />
          <Route path="/register" element={<RegisterPage onAuthed={onAuthed} />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      )}
    </BrowserRouter>
  );
}
