import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const NAV_ITEMS = [
  { to: "/", label: "Overview", end: true },
  { to: "/devices", label: "Dispositivos" },
  { to: "/traffic", label: "Tráfego" },
  { to: "/alerts", label: "Alertas" },
  { to: "/logs", label: "Logs" },
];

const DESKTOP_BREAKPOINT = "(min-width: 1025px)";

function HamburgerIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
      <path d="M2 4.5H16M2 9H16M2 13.5H16" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

export function Layout() {
  const { username, logout } = useAuth();
  // Starts open on desktop (matches the sidebar's historical always-visible
  // behavior) and closed on phones/tablets — computed synchronously so
  // there's no visible flash of the wrong state on first paint.
  const [sidebarOpen, setSidebarOpen] = useState(
    () => typeof window !== "undefined" && window.matchMedia(DESKTOP_BREAKPOINT).matches
  );
  const location = useLocation();

  // Only auto-close on navigation for the off-canvas mobile/tablet drawer —
  // on desktop the sidebar is a persistent panel, so picking a page
  // shouldn't collapse it out from under the user.
  useEffect(() => {
    if (!window.matchMedia(DESKTOP_BREAKPOINT).matches) {
      setSidebarOpen(false);
    }
  }, [location.pathname]);

  function toggleSidebar() {
    setSidebarOpen((v) => !v);
  }

  return (
    <div className="app-shell">
      <div className="topbar">
        <button
          className="topbar-menu-btn"
          onClick={toggleSidebar}
          aria-label={sidebarOpen ? "Fechar menu" : "Abrir menu"}
          aria-expanded={sidebarOpen}
        >
          <HamburgerIcon />
        </button>
        <div className="topbar-title">NetSentinel</div>
      </div>

      {/* Desktop-only: reappears here once the sidebar is collapsed, since
          the topbar hamburger above is hidden at desktop widths. */}
      {!sidebarOpen && (
        <button
          className="sidebar-expand-fab"
          onClick={toggleSidebar}
          aria-label="Mostrar menu"
          title="Mostrar menu"
        >
          <HamburgerIcon />
        </button>
      )}

      <div className={`sidebar-backdrop${sidebarOpen ? " open" : ""}`} onClick={() => setSidebarOpen(false)} />

      <nav className={`sidebar${sidebarOpen ? " open" : ""}`}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 8px 24px" }}>
          <div style={{ fontSize: 18, fontWeight: 700, letterSpacing: "-0.01em" }}>NetSentinel</div>
          <button
            className="sidebar-collapse-btn"
            onClick={toggleSidebar}
            aria-label="Esconder menu"
            title="Esconder menu"
          >
            <HamburgerIcon />
          </button>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 2, flex: 1 }}>
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              style={({ isActive }) => ({
                padding: "9px 12px",
                borderRadius: "var(--radius-sm)",
                fontSize: 14,
                textDecoration: "none",
                color: isActive ? "var(--text-primary)" : "var(--text-secondary)",
                background: isActive ? "var(--surface-2)" : "transparent",
                fontWeight: isActive ? 600 : 400,
              })}
            >
              {item.label}
            </NavLink>
          ))}
        </div>
        <div style={{ borderTop: "1px solid var(--border)", paddingTop: 12, fontSize: 13 }}>
          <div className="text-secondary" style={{ marginBottom: 8 }}>
            {username}
          </div>
          <button
            onClick={() => logout()}
            style={{
              background: "transparent",
              border: "1px solid var(--border)",
              color: "var(--text-secondary)",
              borderRadius: "var(--radius-sm)",
              padding: "6px 10px",
              fontSize: 13,
              width: "100%",
            }}
          >
            Sair
          </button>
        </div>
      </nav>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
