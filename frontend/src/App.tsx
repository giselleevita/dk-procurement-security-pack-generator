import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { useMe } from "./hooks/useMe";
import type { Me } from "./api/types";
import { LoginPage } from "./pages/Login";
import { RegisterPage } from "./pages/Register";
import { DashboardPage } from "./pages/Dashboard";
import { ConnectionsPage } from "./pages/Connections";
import { ControlDetailPage } from "./pages/ControlDetail";
import { Shell } from "./components/Shell";

export default function App() {
  const { me, setMe, loading } = useMe();

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
        <Shell me={me} onLoggedOut={onLoggedOut}>
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/connections" element={<ConnectionsPage />} />
            <Route path="/controls/:key" element={<ControlDetailPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Shell>
      ) : (
        <Routes>
          <Route path="/login" element={<LoginPage onAuthed={onAuthed} />} />
          <Route path="/register" element={<RegisterPage onAuthed={onAuthed} />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      )}
    </BrowserRouter>
  );
}

