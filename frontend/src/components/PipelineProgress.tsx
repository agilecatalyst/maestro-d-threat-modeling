const STEPS = [
  { key: "summary", label: "Summary", states: ["SUMMARIZED", "ASSETS_DONE", "FLOWS_DONE", "THREATS_DONE", "COMPLETE"] },
  { key: "assets", label: "Assets", states: ["ASSETS_DONE", "FLOWS_DONE", "THREATS_DONE", "COMPLETE"] },
  { key: "flows", label: "Flows", states: ["FLOWS_DONE", "THREATS_DONE", "COMPLETE"] },
  { key: "threats", label: "Threats", states: ["THREATS_DONE", "COMPLETE"] },
  { key: "done", label: "Complete", states: ["COMPLETE"] },
];

const ORDER = ["PENDING", "PROCESSING", "SUMMARIZED", "ASSETS_DONE", "FLOWS_DONE", "THREATS_DONE", "COMPLETE"];

function stepClass(current: string, stepStates: string[]) {
  if (stepStates.includes(current)) return "done";
  const currentIdx = ORDER.indexOf(current);
  const firstDoneIdx = Math.min(...stepStates.map((s) => ORDER.indexOf(s)).filter((i) => i >= 0));
  if (currentIdx >= 0 && firstDoneIdx >= 0 && currentIdx + 1 === firstDoneIdx) return "active";
  if (current === "PROCESSING" && stepStates[0] === "SUMMARIZED") return "active";
  return "";
}

export function PipelineProgress({ state, error }: { state: string; error?: string | null }) {
  if (state === "FAILED") {
    return (
      <div className="error-banner">
        Pipeline failed{error ? `: ${error}` : " — check agent logs or retry."}
      </div>
    );
  }

  return (
    <div className="pipeline" role="list" aria-label="Pipeline progress">
      {STEPS.map((step) => (
        <div
          key={step.key}
          className={`pipeline-step ${stepClass(state, step.states)}`}
          role="listitem"
        >
          {step.label}
        </div>
      ))}
    </div>
  );
}
