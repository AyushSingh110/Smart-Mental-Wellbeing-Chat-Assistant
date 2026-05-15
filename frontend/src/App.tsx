import { Navigate, Route, Routes } from "react-router-dom";

import { AppShell } from "./components/layout/AppShell";
import { useAuth } from "./lib/auth";
import { AvatarSelectionPage } from "./pages/AvatarSelectionPage";
import { ChatPage } from "./pages/ChatPage";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
import { ProfilePage } from "./pages/ProfilePage";
import { SettingsPage } from "./pages/SettingsPage";

function ProtectedApp() {
  const { user } = useAuth();

  // Show avatar selection once if the user hasn't chosen an avatar yet
  // (avatarId is stored in DB; if still "therapist" AND this is a new session flag, show selection)
  // We detect "new user" by checking localStorage for avatar_chosen flag
  const avatarChosen = window.localStorage.getItem(`avatar_chosen_${user?.id}`);
  if (!avatarChosen && user) {
    return (
      <Routes>
        <Route path="*" element={<AvatarSelectionPage />} />
      </Routes>
    );
  }

  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/avatar-setup" element={<AvatarSelectionPage />} />
      </Routes>
    </AppShell>
  );
}

export default function App() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div
        className="flex min-h-screen items-center justify-center px-6"
        style={{ background: "#0c1220" }}
      >
        <div
          className="rounded-[24px] px-8 py-7 text-center"
          style={{ background: "#172032", border: "1px solid rgba(55,75,105,0.5)" }}
        >
          <p className="label-caps" style={{ color: "#4a84d6" }}>Preparing</p>
          <h1
            className="mt-3 text-2xl font-semibold text-white"
            style={{ fontFamily: "'Space Grotesk', sans-serif" }}
          >
            Loading your workspace
          </h1>
          <p className="mt-3 text-sm" style={{ color: "#7a92a8" }}>
            Bringing together your latest progress and secure session.
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
