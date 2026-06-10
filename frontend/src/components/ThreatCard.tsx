import type { Threat } from "../types";

function strideClass(category: string) {
  return `stride-${category.toLowerCase().replace(/\s+/g, "-")}`;
}

export function StrideBadge({ category }: { category: string }) {
  return <span className={`stride-badge ${strideClass(category)}`}>{category}</span>;
}

type Props = {
  threat: Threat;
  editable?: boolean;
  onEdit?: () => void;
  onDelete?: () => void;
};

export function ThreatCard({ threat, editable, onEdit, onDelete }: Props) {
  return (
    <article className="threat-card">
      <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
        <h3>{threat.name}</h3>
        <StrideBadge category={threat.stride_category} />
        <span className="state-badge pending">{threat.likelihood}</span>
        {editable && (
          <span style={{ marginLeft: "auto", display: "flex", gap: "0.35rem" }}>
            <button type="button" className="btn btn-ghost" style={{ padding: "0.25rem 0.55rem" }} onClick={onEdit}>
              Edit
            </button>
            <button type="button" className="btn btn-ghost" style={{ padding: "0.25rem 0.55rem" }} onClick={onDelete}>
              Delete
            </button>
          </span>
        )}
      </div>
      <p>{threat.description}</p>
      <p>
        <strong>Target:</strong> {threat.target} · <strong>Source:</strong> {threat.source}
      </p>
      <p>
        <strong>Vector:</strong> {threat.vector}
      </p>
      {threat.mitigations?.length > 0 && (
        <p>
          <strong>Mitigations:</strong> {threat.mitigations.join("; ")}
        </p>
      )}
    </article>
  );
}
