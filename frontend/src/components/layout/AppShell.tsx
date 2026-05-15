import {
  HeartPulse,
  LayoutDashboard,
  MessageSquareText,
  Settings,
  ShieldCheck,
  UserCircle2,
} from "lucide-react";
import clsx from "clsx";
import type { PropsWithChildren } from "react";
import { NavLink } from "react-router-dom";

import { useAuth } from "../../lib/auth";
import type { NavItem } from "../../types";

const navItems: NavItem[] = [
  { label: "Dashboard", path: "/dashboard", description: "Scores, trends, and recent sessions" },
  { label: "Chat",      path: "/chat",      description: "Guided support and check-ins" },
  { label: "Profile",   path: "/profile",   description: "Account and personal overview" },
  { label: "Settings",  path: "/settings",  description: "Preferences and controls" },
];

const iconMap = {
  Dashboard: LayoutDashboard,
  Chat:      MessageSquareText,
  Profile:   UserCircle2,
  Settings:  Settings,
};

export function AppShell({ children }: PropsWithChildren) {
  const { user, logout } = useAuth();
  const userLabel = user?.name?.split(" ")[0] ?? "User";

  return (
    <div className="min-h-screen" style={{ background: "#0c1220" }}>
      <div className="relative mx-auto flex min-h-screen max-w-[1560px]">

        {/* ── SIDEBAR ─────────────────────────────────────── */}
        <aside
          className="sticky top-0 hidden h-screen w-[240px] shrink-0 flex-col xl:flex"
          style={{
            background: "#111c2e",
            borderRight: "1px solid rgba(55,75,105,0.4)",
          }}
        >
          {/* Brand */}
          <div className="flex items-center gap-3 px-5 py-5">
            <div
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg"
              style={{ background: "#4a84d6" }}
            >
              <HeartPulse className="h-4 w-4 text-white" strokeWidth={2.5} />
            </div>
            <div>
              <p className="text-[14px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                Well-Being AI
              </p>
              <p className="text-[10px]" style={{ color: "#4a6278" }}>Mental wellness companion</p>
            </div>
          </div>

          {/* Divider */}
          <div className="mx-5" style={{ height: "1px", background: "rgba(55,75,105,0.4)" }} />

          {/* Nav */}
          <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-0.5">
            <p className="px-3 pb-2 text-[10px] font-bold uppercase tracking-[0.2em]" style={{ color: "#4a6278" }}>
              Navigation
            </p>
            {navItems.map((item) => {
              const Icon = iconMap[item.label as keyof typeof iconMap];
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    clsx(
                      "group flex items-center gap-3 rounded-xl px-3 py-2.5 transition-all duration-150",
                      isActive
                        ? "text-white"
                        : "text-[#7a92a8] hover:text-[#c8d8ea]",
                    )
                  }
                  style={({ isActive }) => ({
                    background: isActive ? "rgba(74,132,214,0.15)" : "transparent",
                    border: isActive ? "1px solid rgba(74,132,214,0.25)" : "1px solid transparent",
                  })}
                >
                  {({ isActive }) => (
                    <>
                      <div
                        className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg transition-colors"
                        style={{
                          background: isActive ? "rgba(74,132,214,0.2)" : "rgba(255,255,255,0.04)",
                          color: isActive ? "#4a84d6" : undefined,
                        }}
                      >
                        <Icon className="h-3.5 w-3.5" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p
                          className="text-[13px] font-medium leading-none"
                          style={{ fontFamily: "'Space Grotesk', sans-serif" }}
                        >
                          {item.label}
                        </p>
                        <p className="mt-0.5 truncate text-[10px]" style={{ color: isActive ? "#7a92a8" : "#4a6278" }}>
                          {item.description}
                        </p>
                      </div>
                      {isActive && (
                        <div className="h-1.5 w-1.5 shrink-0 rounded-full" style={{ background: "#4a84d6" }} />
                      )}
                    </>
                  )}
                </NavLink>
              );
            })}
          </nav>

          {/* Bottom section */}
          <div className="px-3 py-4 space-y-3">
            {/* Security indicator */}
            <div
              className="flex items-center gap-2 rounded-xl px-3 py-2.5"
              style={{ background: "rgba(61,138,92,0.08)", border: "1px solid rgba(61,138,92,0.2)" }}
            >
              <ShieldCheck className="h-3.5 w-3.5 shrink-0" style={{ color: "#3d8a5c" }} />
              <p className="text-[11px]" style={{ color: "#3d8a5c" }}>Secure session active</p>
            </div>

            {/* User card */}
            <div
              className="rounded-xl p-3"
              style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(55,75,105,0.4)" }}
            >
              <div className="flex items-center gap-2.5">
                {user?.picture ? (
                  <img src={user.picture} alt={user.name} className="h-8 w-8 rounded-lg object-cover" />
                ) : (
                  <div
                    className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-xs font-bold text-white"
                    style={{ background: "#4a84d6" }}
                  >
                    {user?.avatar ?? userLabel[0]}
                  </div>
                )}
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[12px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                    {user?.name ?? "User"}
                  </p>
                  <p className="truncate text-[10px]" style={{ color: "#4a6278" }}>{user?.email}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={logout}
                className="mt-2.5 w-full rounded-lg py-1.5 text-[11px] font-medium transition-all duration-150"
                style={{
                  background: "rgba(255,255,255,0.03)",
                  border: "1px solid rgba(55,75,105,0.35)",
                  color: "#7a92a8",
                }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLElement).style.color = "#c8d8ea";
                  (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.06)";
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLElement).style.color = "#7a92a8";
                  (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.03)";
                }}
              >
                Sign out
              </button>
            </div>
          </div>
        </aside>

        {/* ── MAIN CONTENT ────────────────────────────────── */}
        <div className="flex flex-1 flex-col min-h-screen">

          {/* Mobile top bar */}
          <div
            className="xl:hidden flex items-center justify-between px-4 py-3"
            style={{
              background: "#111c2e",
              borderBottom: "1px solid rgba(55,75,105,0.4)",
            }}
          >
            <div className="flex items-center gap-2.5">
              <div
                className="flex h-7 w-7 items-center justify-center rounded-lg"
                style={{ background: "#4a84d6" }}
              >
                <HeartPulse className="h-3.5 w-3.5 text-white" />
              </div>
              <p className="text-[13px] font-semibold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                Well-Being AI
              </p>
            </div>
            {user?.picture ? (
              <img src={user.picture} alt={user.name} className="h-8 w-8 rounded-lg object-cover" />
            ) : (
              <div
                className="flex h-8 w-8 items-center justify-center rounded-lg text-xs font-bold text-white"
                style={{ background: "#4a84d6" }}
              >
                {user?.avatar ?? userLabel[0]}
              </div>
            )}
          </div>

          {/* Mobile bottom nav */}
          <nav
            className="xl:hidden fixed bottom-0 inset-x-0 flex z-40"
            style={{
              background: "#111c2e",
              borderTop: "1px solid rgba(55,75,105,0.4)",
            }}
          >
            {navItems.map((item) => {
              const Icon = iconMap[item.label as keyof typeof iconMap];
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    clsx(
                      "flex flex-1 flex-col items-center gap-1 py-3 text-[10px] font-medium transition-all",
                      isActive ? "text-[#4a84d6]" : "text-[#4a6278]",
                    )
                  }
                >
                  <Icon className="h-4 w-4" />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </nav>

          {/* Page content */}
          <main className="flex-1 overflow-auto p-4 pb-20 sm:p-6 xl:p-8 xl:pb-8">
            {children}
          </main>
        </div>
      </div>
    </div>
  );
}
