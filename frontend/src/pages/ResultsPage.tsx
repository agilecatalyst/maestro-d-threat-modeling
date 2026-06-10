import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import {
  getThreatModel,
  pollUntilComplete,
  downloadExport,
  mutateThreats,
  scanFlowThreats,
  PollTimeoutError,
} from "../api/client";
import { PipelineProgress } from "../components/PipelineProgress";
import { StateBadge } from "../components/Layout";
import { SentryDrawer } from "../components/SentryDrawer";
import { ThreatCard } from "../components/ThreatCard";
import { ThreatEditorModal } from "../components/ThreatEditorModal";
import { isSentryEnabled } from "../config";
import type { DataFlow, Threat, ThreatModelResult } from "../types";

type Tab = "summary" | "assets" | "flows" | "threats";

export function ResultsPage() {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const shouldPoll = searchParams.get("running") === "1";

  const [model, setModel] = useState<ThreatModelResult | null>(null);
  const [liveState, setLiveState] = useState<string>("PROCESSING");
  const [tab, setTab] = useState<Tab>("summary");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exportBusy, setExportBusy] = useState<"pdf" | "json" | null>(null);
  const [editorOpen, setEditorOpen] = useState(false);
  const [editingThreat, setEditingThreat] = useState<Threat | null>(null);
  const [sentryOpen, setSentryOpen] = useState(false);
  const [flowScanBusy, setFlowScanBusy] = useState<string | null>(null);
  const [mutationBusy, setMutationBusy] = useState(false);

  const load = async (modelId: string) => {
    const data = await getThreatModel(modelId);
    setModel(data);
    setLiveState(data.state);
    return data;
  };

  useEffect(() => {
    if (!id) return;
    let cancelled = false;

    const run = async () => {
      setLoading(true);
      setError(null);
      try {
        if (shouldPoll) {
          try {
            await pollUntilComplete(id, (state) => {
              if (!cancelled) setLiveState(state);
            });
          } catch (err) {
            if (err instanceof PollTimeoutError && !cancelled) {
              await load(id);
              setError(
                "Local LLM is still working — refresh in a minute or wait for threats to finish.",
              );
              return;
            }
            throw err;
          }
        }
        if (!cancelled) await load(id);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load results");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void run();
    return () => {
      cancelled = true;
    };
  }, [id, shouldPoll]);

  const state = model?.state ?? liveState;
  const isRunning = state !== "COMPLETE" && state !== "FAILED";
  const canExport = state === "COMPLETE";
  const canEdit = state === "COMPLETE" || state === "THREATS_DONE";

  const applyMutationResult = (result: { threats: Threat[]; meta?: ThreatModelResult["meta"] }) => {
    setModel((prev) =>
      prev
        ? {
            ...prev,
            threats: result.threats,
            meta: result.meta ?? prev.meta,
          }
        : prev,
    );
  };

  const handleExport = async (format: "pdf" | "json") => {
    if (!id) return;
    setExportBusy(format);
    setError(null);
    try {
      await downloadExport(id, format);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed");
    } finally {
      setExportBusy(null);
    }
  };

  const openAddThreat = () => {
    setEditingThreat(null);
    setEditorOpen(true);
  };

  const openEditThreat = (threat: Threat) => {
    setEditingThreat(threat);
    setEditorOpen(true);
  };

  const handleSaveThreat = async (threat: Threat) => {
    if (!id) return;
    setMutationBusy(true);
    setError(null);
    try {
      const result = await mutateThreats(id, editingThreat ? "update" : "add", [threat]);
      applyMutationResult(result);
      setEditorOpen(false);
      setEditingThreat(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save threat");
    } finally {
      setMutationBusy(false);
    }
  };

  const handleDeleteThreat = async (threat: Threat) => {
    if (!id || !window.confirm(`Delete "${threat.name}"?`)) return;
    setMutationBusy(true);
    setError(null);
    try {
      const result = await mutateThreats(id, "delete", [threat]);
      applyMutationResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete threat");
    } finally {
      setMutationBusy(false);
    }
  };

  const handleScanFlow = async (flow: DataFlow) => {
    if (!id) return;
    const key = `${flow.source_entity}-${flow.target_entity}`;
    setFlowScanBusy(key);
    setError(null);
    try {
      const result = await scanFlowThreats(id, {
        source_entity: flow.source_entity,
        target_entity: flow.target_entity,
        flow_description: flow.flow_description,
      });
      applyMutationResult(result);
      if (result.added > 0) {
        setTab("threats");
      } else {
        setError("No new threats found for this flow — try Sentry or add manually.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Flow scan failed");
    } finally {
      setFlowScanBusy(null);
    }
  };

  return (
    <div className={`results-layout ${sentryOpen ? "with-sentry" : ""}`}>
      <section className="panel results-main">
        <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", flexWrap: "wrap" }}>
          <div>
            <h2>{model?.title || "Threat model"}</h2>
            <p className="subtitle" style={{ marginBottom: 0 }}>
              <span style={{ fontFamily: "var(--mono)", fontSize: "0.82rem" }}>{id}</span>
            </p>
          </div>
          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
            {canExport && isSentryEnabled() && (
              <button type="button" className="btn btn-primary" onClick={() => setSentryOpen(true)}>
                AI
              </button>
            )}
            <StateBadge state={state} />
          </div>
        </div>

      {error && <div className="error-banner">{error}</div>}

      {canEdit && (
        <p className="review-disclaimer">
          AI-generated starting point — review all threats and mitigations before backlog or audit use.
          See <a href="https://github.com/agilecatalyst/maestro-d-threat-modeling/blob/main/SECURITY.md" target="_blank" rel="noreferrer">SECURITY.md</a>
          {" · "}
          <a href="https://github.com/agilecatalyst/maestro-d-threat-modeling/blob/main/NOTICE" target="_blank" rel="noreferrer">NOTICE</a>
          {" · "}
          <a href="https://github.com/agilecatalyst/maestro-d-threat-modeling/blob/main/LICENSE" target="_blank" rel="noreferrer">Apache-2.0</a>
        </p>
      )}

      {(loading || (shouldPoll && isRunning)) && (
          <>
            <PipelineProgress state={liveState} />
            <div className="empty">
              <div className="spinner" style={{ margin: "0 auto 0.75rem" }} />
              {isRunning
                ? `Agent is analyzing (${liveState.replace(/_/g, " ").toLowerCase()})…`
                : "Loading results…"}
            </div>
          </>
        )}

        {!loading && model && (
          <>
            <PipelineProgress state={state} />

            {model.meta && (
              <div className="meta-grid">
                <div className="meta-item">
                  <span>Threats</span>
                  <strong>{model.meta.threat_count ?? model.threats?.length ?? 0}</strong>
                </div>
                {model.meta.stride_counts &&
                  Object.entries(model.meta.stride_counts).slice(0, 3).map(([k, v]) => (
                    <div className="meta-item" key={k}>
                      <span>{k}</span>
                      <strong>{v}</strong>
                    </div>
                  ))}
              </div>
            )}

            <div className="tabs">
              {(["summary", "assets", "flows", "threats"] as Tab[]).map((key) => (
                <button
                  key={key}
                  type="button"
                  className={`tab ${tab === key ? "active" : ""}`}
                  onClick={() => setTab(key)}
                >
                  {key.charAt(0).toUpperCase() + key.slice(1)}
                  {key === "threats" && model.threats ? ` (${model.threats.length})` : ""}
                </button>
              ))}
            </div>

            {tab === "summary" && (
              <div>
                {model.summary ? (
                  <p style={{ whiteSpace: "pre-wrap", lineHeight: 1.65 }}>{model.summary}</p>
                ) : (
                  <p className="empty">No summary yet.</p>
                )}
              </div>
            )}

            {tab === "assets" && (
              <div className="table-wrap">
                {(model.assets?.length ?? 0) > 0 ? (
                  <table>
                    <thead>
                      <tr>
                        <th>Type</th>
                        <th>Name</th>
                        <th>Criticality</th>
                        <th>Description</th>
                      </tr>
                    </thead>
                    <tbody>
                      {model.assets!.map((asset) => (
                        <tr key={asset.name}>
                          <td>{asset.type}</td>
                          <td>{asset.name}</td>
                          <td>{asset.criticality}</td>
                          <td>{asset.description}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <p className="empty">No assets identified.</p>
                )}
              </div>
            )}

            {tab === "flows" && (
              <div className="grid-cards">
                {(model.flows?.data_flows?.length ?? 0) > 0 ? (
                  model.flows!.data_flows!.map((flow, index) => {
                    const scanKey = `${flow.source_entity}-${flow.target_entity}`;
                    return (
                      <div className="threat-card" key={`${flow.source_entity}-${index}`}>
                        <h3>{flow.source_entity} → {flow.target_entity}</h3>
                        <p>{flow.flow_description}</p>
                        {canEdit && (
                          <button
                            type="button"
                            className="btn btn-ghost"
                            disabled={flowScanBusy !== null || mutationBusy}
                            onClick={() => void handleScanFlow(flow)}
                          >
                            {flowScanBusy === scanKey ? "Scanning…" : "Find threats for this flow"}
                          </button>
                        )}
                      </div>
                    );
                  })
                ) : (
                  <p className="empty">No data flows yet.</p>
                )}
                {(model.flows?.threat_sources?.length ?? 0) > 0 && (
                  <>
                    <h3 style={{ marginTop: "1rem" }}>Threat actors</h3>
                    <div className="table-wrap">
                      <table>
                        <thead>
                          <tr>
                            <th>Category</th>
                            <th>Description</th>
                            <th>Examples</th>
                          </tr>
                        </thead>
                        <tbody>
                          {model.flows!.threat_sources!.map((source) => (
                            <tr key={source.category}>
                              <td>{source.category}</td>
                              <td>{source.description}</td>
                              <td>{source.example}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </>
                )}
              </div>
            )}

            {tab === "threats" && (
              <>
                {canEdit && (
                  <div className="actions-row" style={{ marginTop: 0, marginBottom: "0.75rem" }}>
                    <button
                      type="button"
                      className="btn btn-primary"
                      disabled={mutationBusy}
                      onClick={openAddThreat}
                    >
                      + Add threat
                    </button>
                  </div>
                )}
                <div className="grid-cards">
                  {(model.threats?.length ?? 0) > 0 ? (
                    model.threats!.map((threat) => (
                      <ThreatCard
                        key={threat.name}
                        threat={threat}
                        editable={canEdit}
                        onEdit={() => openEditThreat(threat)}
                        onDelete={() => void handleDeleteThreat(threat)}
                      />
                    ))
                  ) : (
                    <p className="empty">No threats in catalog yet.</p>
                  )}
                </div>
              </>
            )}

            <div className="actions-row">
              <Link to="/" className="btn btn-ghost">
                ← Back to catalog
              </Link>
              {!isRunning && (
                <button type="button" className="btn btn-ghost" onClick={() => id && void load(id)}>
                  Refresh
                </button>
              )}
              {canExport && (
                <>
                  <button
                    type="button"
                    className="btn btn-primary"
                    disabled={exportBusy !== null}
                    onClick={() => void handleExport("pdf")}
                  >
                    {exportBusy === "pdf" ? "Generating PDF…" : "Download PDF"}
                  </button>
                  <button
                    type="button"
                    className="btn btn-ghost"
                    disabled={exportBusy !== null}
                    onClick={() => void handleExport("json")}
                  >
                    {exportBusy === "json" ? "Exporting…" : "Download JSON"}
                  </button>
                </>
              )}
            </div>
          </>
        )}

        <ThreatEditorModal
          open={editorOpen}
          threat={editingThreat}
          onClose={() => {
            setEditorOpen(false);
            setEditingThreat(null);
          }}
          onSave={(threat) => void handleSaveThreat(threat)}
        />
      </section>

      {model && id && sentryOpen && (
        <SentryDrawer
          open={sentryOpen}
          threatModelId={id}
          model={model}
          onClose={() => setSentryOpen(false)}
          onCatalogChanged={() => void load(id)}
        />
      )}
    </div>
  );
}
