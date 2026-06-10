import { useEffect, useState } from "react";
import type { Threat } from "../types";

const STRIDE_OPTIONS = [
  "Spoofing",
  "Tampering",
  "Repudiation",
  "Information Disclosure",
  "Denial of Service",
  "Elevation of Privilege",
];

const LIKELIHOOD_OPTIONS = ["Low", "Medium", "High"];

function emptyThreat(): Threat {
  return {
    name: "",
    stride_category: "Tampering",
    description: "",
    target: "",
    source: "External Threat Actors",
    likelihood: "Medium",
    impact: "",
    mitigations: [""],
    prerequisites: [""],
    vector: "",
  };
}

type Props = {
  open: boolean;
  threat: Threat | null;
  onClose: () => void;
  onSave: (threat: Threat) => void;
};

export function ThreatEditorModal({ open, threat, onClose, onSave }: Props) {
  const [draft, setDraft] = useState<Threat>(emptyThreat());

  useEffect(() => {
    if (open) {
      setDraft(threat ? { ...threat } : emptyThreat());
    }
  }, [open, threat]);

  if (!open) return null;

  const update = (field: keyof Threat, value: string | string[]) => {
    setDraft((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    const mitigations = draft.mitigations.map((m) => m.trim()).filter(Boolean);
    const prerequisites = draft.prerequisites.map((p) => p.trim()).filter(Boolean);
    onSave({
      ...draft,
      mitigations: mitigations.length ? mitigations : ["Apply defense in depth"],
      prerequisites,
    });
  };

  return (
    <div className="modal-backdrop" role="presentation" onClick={onClose}>
      <form
        className="modal-panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="threat-editor-title"
        onClick={(event) => event.stopPropagation()}
        onSubmit={handleSubmit}
      >
        <h3 id="threat-editor-title">{threat ? "Edit threat" : "Add threat"}</h3>

        <label>
          Name
          <input
            required
            value={draft.name}
            onChange={(event) => update("name", event.target.value)}
          />
        </label>

        <div className="modal-grid">
          <label>
            STRIDE
            <select
              value={draft.stride_category}
              onChange={(event) => update("stride_category", event.target.value)}
            >
              {STRIDE_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
          <label>
            Likelihood
            <select
              value={draft.likelihood}
              onChange={(event) => update("likelihood", event.target.value)}
            >
              {LIKELIHOOD_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
        </div>

        <label>
          Description
          <textarea
            required
            rows={3}
            value={draft.description}
            onChange={(event) => update("description", event.target.value)}
          />
        </label>

        <div className="modal-grid">
          <label>
            Target
            <input
              required
              value={draft.target}
              onChange={(event) => update("target", event.target.value)}
            />
          </label>
          <label>
            Source
            <input
              required
              value={draft.source}
              onChange={(event) => update("source", event.target.value)}
            />
          </label>
        </div>

        <label>
          Vector
          <input
            required
            value={draft.vector}
            onChange={(event) => update("vector", event.target.value)}
          />
        </label>

        <label>
          Impact
          <textarea
            required
            rows={2}
            value={draft.impact}
            onChange={(event) => update("impact", event.target.value)}
          />
        </label>

        <label>
          Mitigations (one per line)
          <textarea
            rows={3}
            value={draft.mitigations.join("\n")}
            onChange={(event) => update("mitigations", event.target.value.split("\n"))}
          />
        </label>

        <div className="actions-row">
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn btn-primary">
            Save
          </button>
        </div>
      </form>
    </div>
  );
}
