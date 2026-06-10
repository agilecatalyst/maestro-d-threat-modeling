import { useCallback, useState } from "react";
import type { DragEvent } from "react";
import { useNavigate } from "react-router-dom";
import { startThreatModel, uploadDiagram } from "../api/client";

export function WizardPage() {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [applicationType, setApplicationType] = useState("hybrid");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const pickFile = useCallback((next: File | null) => {
    setFile(next);
    if (preview) URL.revokeObjectURL(preview);
    setPreview(next ? URL.createObjectURL(next) : null);
  }, [preview]);

  const onDrop = (event: DragEvent) => {
    event.preventDefault();
    setDragActive(false);
    const dropped = event.dataTransfer.files?.[0];
    if (dropped && dropped.type.startsWith("image/")) pickFile(dropped);
  };

  const submit = async () => {
    if (!file) {
      setError("Upload an architecture diagram (PNG or JPEG).");
      return;
    }
    if (description.trim().length < 10) {
      setError("Add a description of at least 10 characters.");
      return;
    }

    setBusy(true);
    setError(null);
    try {
      const uploaded = await uploadDiagram(file);
      await startThreatModel({
        id: uploaded.id,
        description: description.trim(),
        title: title.trim() || undefined,
        application_type: applicationType,
      });
      navigate(`/models/${uploaded.id}?running=1`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start job");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="panel">
      <h2>New threat model</h2>
      <p className="subtitle">
        Upload your architecture diagram and describe the system. The local agent runs summary → assets → flows → threats.
      </p>

      {error && <div className="error-banner">{error}</div>}

      <div
        className={`dropzone ${dragActive ? "active" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={onDrop}
        onClick={() => document.getElementById("diagram-input")?.click()}
      >
        <input
          id="diagram-input"
          type="file"
          accept="image/png,image/jpeg"
          hidden
          onChange={(e) => pickFile(e.target.files?.[0] ?? null)}
        />
        {preview ? (
          <>
            <img
              src={preview}
              alt="Diagram preview"
              style={{ maxHeight: 180, maxWidth: "100%", borderRadius: 8, marginBottom: "0.5rem" }}
            />
            <p>
              <strong>{file?.name}</strong> — click to replace
            </p>
          </>
        ) : (
          <>
            <strong>Drop diagram here</strong>
            <p>PNG or JPEG · max 10 MB</p>
          </>
        )}
      </div>

      <div className="field" style={{ marginTop: "1.25rem" }}>
        <label htmlFor="title">Title (optional)</label>
        <input
          id="title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Payment platform v2"
        />
      </div>

      <div className="field">
        <label htmlFor="description">System description</label>
        <textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Three-tier web app: browser, API gateway, PostgreSQL. External payment provider at trust boundary."
        />
      </div>

      <div className="field">
        <label htmlFor="app-type">Application type</label>
        <select id="app-type" value={applicationType} onChange={(e) => setApplicationType(e.target.value)}>
          <option value="hybrid">Hybrid (internal + external)</option>
          <option value="web">Web application</option>
          <option value="api">API / backend service</option>
          <option value="mobile">Mobile + backend</option>
        </select>
      </div>

      <div className="actions-row">
        <button type="button" className="btn btn-primary" disabled={busy} onClick={() => void submit()}>
          {busy ? (
            <>
              <span className="spinner" /> Starting…
            </>
          ) : (
            "Run threat modeling"
          )}
        </button>
      </div>
    </section>
  );
}
