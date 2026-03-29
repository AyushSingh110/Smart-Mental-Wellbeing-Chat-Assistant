import {
  HeartPulse,
  LayoutDashboard,
  MessageSquareText,
  Settings,
  ShieldCheck,
  UserCircle2,
  ChevronRight,
} from "lucide-react";
import clsx from "clsx";
import type { PropsWithChildren } from "react";
import { NavLink, useLocation } from "react-router-dom";

import { useAuth } from "../../lib/auth";
import type { NavItem } from "../../types";

const navItems: NavItem[] = [
  { label: "Dashboard", path: "/dashboard", description: "Scores, trends, and recent sessions" },
  { label: "Chat",      path: "/chat",      description: "Voice-first support and guided check-ins" },
  { label: "Profile",   path: "/profile",   description: "Account, preferences, and personal overview" },
  { label: "Settings",  path: "/settings",  description: "Privacy, notifications, and integrations" },
];

const iconMap = {
  Dashboard: LayoutDashboard,
  Chat:      MessageSquareText,
  Profile:   UserCircle2,
  Settings:  Settings,
};

const pageMeta: Record<string, { eyebrow: string; title: string }> = {
  "/dashboard": { eyebrow: "Daily Overview",       title: "Well-being snapshot" },
  "/chat":      { eyebrow: "Guided Conversation",  title: "Support session"     },
  "/profile":   { eyebrow: "Personal Account",     title: "Your profile"        },
  "/settings":  { eyebrow: "Preferences",          title: "Settings"            },
};

export function AppShell({ children }: PropsWithChildren) {
  const { user, logout } = useAuth();
  const location  = useLocation();
  const page      = pageMeta[location.pathname] ?? pageMeta["/dashboard"];
  const userLabel = user?.name?.split(" ")[0] ?? "You";

  return (
    <div
      className="min-h-screen text-slate-50"
      style={{ background: "#09111f" }}
    >
      {/* Ambient background */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div
          className="absolute left-[6%] top-[8%] h-64 w-64 rounded-full opacity-20"
          style={{ background: "radial-gradient(circle, #6ce3cf, transparent 70%)", filter: "blur(80px)" }}
        />
        <div
          className="absolute bottom-[8%] right-[10%] h-48 w-48 rounded-full opacity-10"
          style={{ background: "radial-gradient(circle, #ffc96b, transparent 70%)", filter: "blur(80px)" }}
        />
      </div>

      <div className="relative mx-auto flex min-h-screen max-w-[1560px] gap-4 p-4 lg:p-5">

        {/* ── SIDEBAR ──────────────────────────────────────── */}
        <aside
          className="sticky top-4 hidden h-[calc(100vh-2rem)] w-[260px] shrink-0 flex-col rounded-[26px] p-4 xl:flex"
          style={{
            background: "rgba(255,255,255,0.028)",
            border: "1px solid rgba(255,255,255,0.07)",
          }}
        >
          {/* Brand */}
          <div className="flex items-center gap-3 px-2 py-1">
            <div
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl"
              style={{ background: "linear-gradient(135deg, #6ce3cf 0%, #1b9db6 100%)" }}
            >
              <HeartPulse className="h-4.5 w-4.5 text-[#09111f]" strokeWidth={2.5} />
            </div>
            <div>
              <p
                className="text-[15px] font-semibold text-white"
                style={{ fontFamily: "'Space Grotesk', sans-serif" }}
              >
                Well-Being AI
              </p>
              <p className="text-[11px] text-slate-500">Private wellness companion</p>
            </div>
          </div>

          {/* Divider */}
          <div className="my-4 h-px" style={{ background: "rgba(255,255,255,0.05)" }} />

          {/* Nav label */}
          <p className="mb-2 px-2 text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-600">
            Workspace
          </p>

          {/* Nav items */}
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = iconMap[item.label as keyof typeof iconMap];
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    clsx(
                      "group flex items-center gap-3 rounded-[14px] px-3 py-2.5 transition-all duration-200",
                      isActive
                        ? "bg-[#6ce3cf]/[0.1] text-white"
                        : "text-slate-400 hover:bg-white/[0.04] hover:text-slate-200",
                    )
                  }
                >
                  {({ isActive }) => (
                    <>
                      <div
                        className={clsx(
                          "flex h-8 w-8 shrink-0 items-center justify-center rounded-[10px] transition-colors",
                          isActive
                            ? "bg-[#6ce3cf]/[0.15] text-[#6ce3cf]"
                            : "bg-white/[0.04] text-slate-500 group-hover:text-slate-300",
                        )}
                      >
                        <Icon className="h-4 w-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p
                          className={clsx(
                            "text-[14px] font-medium leading-none",
                            isActive ? "text-white" : "text-slate-300"
                          )}
                          style={{ fontFamily: "'Space Grotesk', sans-serif" }}
                        >
                          {item.label}
                        </p>
                        <p className="mt-1 truncate text-[11px] text-slate-500">
                          {item.description}
                        </p>
                      </div>
                      {isActive && (
                        <div className="h-1.5 w-1.5 shrink-0 rounded-full bg-[#6ce3cf]" />
                      )}
                    </>
                  )}
                </NavLink>
              );
            })}
          </nav>

          {/* Spacer */}
          <div className="flex-1" />

          {/* Security badge */}
          <div
            className="mb-3 flex items-center gap-2 rounded-[12px] px-3 py-2.5"
            style={{ background: "rgba(108,227,207,0.05)", border: "1px solid rgba(108,227,207,0.1)" }}
          >
            <ShieldCheck className="h-3.5 w-3.5 shrink-0 text-[#6ce3cf]/70" />
            <p className="text-[11px] text-slate-500">Secure workspace active</p>
          </div>

          {/* User card */}
          <div
            className="rounded-[16px] p-3"
            style={{
              background: "rgba(255,255,255,0.03)",
              border: "1px solid rgba(255,255,255,0.07)",
            }}
          >
            <div className="flex items-center gap-3">
              {user?.picture ? (
                <img
                  src={user.picture}
                  alt={user.name}
                  className="h-9 w-9 rounded-[10px] object-cover"
                />
              ) : (
                <div
                  className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[10px] text-xs font-bold text-[#09111f]"
                  style={{ background: "linear-gradient(135deg, #6ce3cf, #1b9db6)" }}
                >
                  {user?.avatar ?? userLabel[0]}
                </div>
              )}
              <div className="min-w-0 flex-1">
                <p
                  className="truncate text-[13px] font-semibold text-white"
                  style={{ fontFamily: "'Space Grotesk', sans-serif" }}
                >
                  {user?.name ?? "User"}
                </p>
                <p className="truncate text-[11px] text-slate-500">{user?.email}</p>
              </div>
            </div>
            <button
              type="button"
              onClick={logout}
              className="mt-3 w-full rounded-[10px] py-2 text-[12px] font-medium text-slate-400 transition-all duration-200 hover:bg-white/[0.06] hover:text-white"
              style={{ border: "1px solid rgba(255,255,255,0.06)" }}
            >
              Sign out
            </button>
          </div>
        </aside>

        {/* ── MAIN ─────────────────────────────────────────── */}
        <main className="flex min-h-[calc(100vh-2rem)] flex-1 flex-col gap-4">

          {/* Mobile top bar */}
          <div
            className="xl:hidden rounded-[20px] p-4"
            style={{
              background: "rgba(255,255,255,0.028)",
              border: "1px solid rgba(255,255,255,0.07)",
            }}
          >
            <div className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div
                  className="flex h-8 w-8 items-center justify-center rounded-[10px]"
                  style={{ background: "linear-gradient(135deg, #6ce3cf, #1b9db6)" }}
                >
                  <HeartPulse className="h-4 w-4 text-[#09111f]" />
                </div>
                <p
                  className="text-[14px] font-semibold text-white"
                  style={{ fontFamily: "'Space Grotesk', sans-serif" }}
                >
                  Well-Being AI
                </p>
              </div>
              {user?.picture ? (
                <img src={user.picture} alt={user.name} className="h-9 w-9 rounded-[10px] object-cover" />
              ) : (
                <div
                  className="flex h-9 w-9 items-center justify-center rounded-[10px] text-xs font-bold text-[#09111f]"
                  style={{ background: "linear-gradient(135deg, #6ce3cf, #1b9db6)" }}
                >
                  {user?.avatar ?? userLabel[0]}
                </div>
              )}
            </div>

            <nav className="mt-4 grid grid-cols-4 gap-1.5">
              {navItems.map((item) => {
                const Icon = iconMap[item.label as keyof typeof iconMap];
                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    className={({ isActive }) =>
                      clsx(
                        "flex flex-col items-center gap-1.5 rounded-[12px] px-2 py-2.5 text-[11px] transition-all",
                        isActive
                          ? "bg-[#6ce3cf]/[0.1] text-[#6ce3cf]"
                          : "text-slate-500 hover:bg-white/[0.04] hover:text-slate-300",
                      )
                    }
                  >
                    <Icon className="h-4 w-4" />
                    <span>{item.label}</span>
                  </NavLink>
                );
              })}
            </nav>
          </div>

          {/* Page content wrapper */}
          <div
            className="flex flex-1 flex-col rounded-[26px] overflow-hidden"
            style={{
              background: "rgba(255,255,255,0.022)",
              border: "1px solid rgba(255,255,255,0.07)",
            }}
          >
            {/* Page header */}
            <header
              className="flex items-center justify-between px-6 py-4 lg:px-8 lg:py-5"
              style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}
            >
              <div className="flex items-center gap-3">
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-[#6ce3cf]/70">
                    {page.eyebrow}
                  </p>
                  <h1
                    className="mt-0.5 text-[18px] font-semibold text-white"
                    style={{ fontFamily: "'Space Grotesk', sans-serif" }}
                  >
                    {page.title}
                  </h1>
                </div>
              </div>

              {/* Right side — user chip */}
              <div className="flex items-center gap-2.5">
                <div className="hidden sm:block text-right">
                  <p className="text-[13px] font-medium text-white">
                    {userLabel}
                  </p>
                  <p className="text-[11px] text-slate-500">Personal workspace</p>
                </div>
                {user?.picture ? (
                  <img
                    src={user.picture}
                    alt={user.name}
                    className="h-9 w-9 rounded-[10px] object-cover"
                  />
                ) : (
                  <div
                    className="flex h-9 w-9 items-center justify-center rounded-[10px] text-xs font-bold text-[#09111f]"
                    style={{ background: "linear-gradient(135deg, #6ce3cf, #1b9db6)" }}
                  >
                    {user?.avatar ?? userLabel[0]}
                  </div>
                )}
                <ChevronRight className="h-4 w-4 text-slate-600" />
              </div>
            </header>

            {/* Page body */}
            <div className="flex-1 overflow-auto p-5 sm:p-6 lg:p-8">
              {children}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}