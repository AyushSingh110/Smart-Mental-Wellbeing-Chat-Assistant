import { Navigate, Route, Routes } from "react-router-dom";

import { AppShell } from "./components/layout/AppShell";
import { useAuth } from "./lib/auth";
import { ChatPage } from "./pages/ChatPage";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
import { ProfilePage } from "./pages/ProfilePage";
import { SettingsPage } from "./pages/SettingsPage";

function ProtectedApp() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Routes>
    </AppShell>
  );
}

export default function App() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-ink px-6 text-slate-200">
        <div className="surface-card animate-rise-in rounded-[32px] border border-white/10 px-8 py-7 text-center shadow-halo">
          <p className="text-xs uppercase tracking-[0.34em] text-brand-300">Preparing</p>
          <h1 className="mt-3 font-display text-2xl font-semibold text-white">
            Loading your calm workspace
          </h1>
          <p className="mt-3 text-sm text-slate-400">
            Bringing together your latest progress, history, and secure session.
          </p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return <ProtectedApp />;
}
