import { useEffect, useState, type MouseEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { deleteThreatModel, listThreatModels } from "../api/client";
import { StateBadge } from "../components/Layout";
import type { ThreatModelListItem } from "../types";

function formatWhen(iso?: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export function CatalogPage() {
  const navigate = useNavigate();
  const [items, setItems] = useState<ThreatModelListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const refresh = () => {
    setLoading(true);
    listThreatModels()
      .then((data) => setItems(data.items))
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    refresh();
  }, []);

  const handleDelete = async (item: ThreatModelListItem, event: MouseEvent) => {
    event.stopPropagation();
    if (!window.confirm(`Delete "${item.title || "Untitled model"}" permanently?`)) return;
    setDeletingId(item.id);
    setError(null);
    try {
      await deleteThreatModel(item.id);
      setItems((prev) => prev.filter((row) => row.id !== item.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <section className="panel">
      <h2>Threat model catalog</h2>
      <p className="subtitle">Recent analyses on this machine — local Postgres, no cloud lock-in.</p>

      {error && <div className="error-banner">{error}</div>}

      {loading && (
        <div className="empty">
          <div className="spinner" style={{ margin: "0 auto 0.75rem" }} />
          Loading catalog…
        </div>
      )}

      {!loading && items.length === 0 && (
        <div className="empty">
          No models yet.{" "}
          <Link to="/new">Start your first threat model</Link>
        </div>
      )}

      {!loading && items.length > 0 && (
        <div className="grid-cards">
          {items.map((item) => (
            <div
              key={item.id}
              className="catalog-row"
              role="button"
              tabIndex={0}
              onClick={() => navigate(`/models/${item.id}`)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") navigate(`/models/${item.id}`);
              }}
              style={{ cursor: "pointer" }}
            >
              <div style={{ flex: 1 }}>
                <strong>{item.title || "Untitled model"}</strong>
                <div className="id">{item.id}</div>
                <div style={{ fontSize: "0.82rem", color: "var(--text-muted)", marginTop: "0.35rem" }}>
                  Updated {formatWhen(item.updated_at)}
                  {item.threat_count != null ? ` · ${item.threat_count} threats` : ""}
                </div>
              </div>
              <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                <StateBadge state={item.state} />
                <button
                  type="button"
                  className="btn btn-ghost"
                  disabled={deletingId === item.id}
                  onClick={(e) => void handleDelete(item, e)}
                  aria-label={`Delete ${item.title || "model"}`}
                >
                  {deletingId === item.id ? "…" : "Delete"}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="actions-row">
        <Link to="/new" className="btn btn-primary">
          + New threat model
        </Link>
        {!loading && items.length > 0 && (
          <button type="button" className="btn btn-ghost" onClick={refresh}>
            Refresh
          </button>
        )}
      </div>
    </section>
  );
}
