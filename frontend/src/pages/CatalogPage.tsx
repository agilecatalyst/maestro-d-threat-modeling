import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listThreatModels } from "../api/client";
import { StateBadge } from "../components/Layout";
import type { ThreatModelListItem } from "../types";

export function CatalogPage() {
  const [items, setItems] = useState<ThreatModelListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listThreatModels()
      .then((data) => setItems(data.items))
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

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
            <Link key={item.id} to={`/models/${item.id}`} style={{ textDecoration: "none", color: "inherit" }}>
              <div className="catalog-row">
                <div>
                  <strong>{item.title || "Untitled model"}</strong>
                  <div className="id">{item.id}</div>
                </div>
                <StateBadge state={item.state} />
              </div>
            </Link>
          ))}
        </div>
      )}

      <div className="actions-row">
        <Link to="/new" className="btn btn-primary">
          + New threat model
        </Link>
      </div>
    </section>
  );
}
