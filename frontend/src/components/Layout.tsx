import type { ReactNode } from "react";
import { Link, NavLink, Outlet } from "react-router-dom";
import { StackHealth } from "./StackHealth";

export function Layout() {
  return (
    <div className="shell">
      <header className="header">
        <div className="brand">
          <div className="brand-mark" aria-hidden>
            MD
          </div>
          <div>
            <h1>Maestro&apos;D ThreatModeling</h1>
            <p>Local-first STRIDE threat modeling</p>
          </div>
        </div>
        <nav className="nav">
          <NavLink to="/" end className={({ isActive }) => (isActive ? "active" : "")}>
            Catalog
          </NavLink>
          <NavLink to="/new" className={({ isActive }) => (isActive ? "active" : "")}>
            New model
          </NavLink>
        </nav>
      </header>
      <Outlet />
      <footer style={{ marginTop: "2.5rem", color: "var(--text-muted)", fontSize: "0.8rem" }}>
        Maestro&apos;D · OWASP-oriented · inference stays on your machine · <StackHealth />
      </footer>
    </div>
  );
}

export function StateBadge({ state }: { state: string }) {
  const cls =
    state === "COMPLETE"
      ? "complete"
      : state === "FAILED"
        ? "failed"
        : state === "PENDING"
          ? "pending"
          : "processing";
  return <span className={`state-badge ${cls}`}>{state.replace(/_/g, " ")}</span>;
}

export function LinkButton({ to, children }: { to: string; children: ReactNode }) {
  return (
    <Link to={to} className="btn btn-ghost">
      {children}
    </Link>
  );
}
