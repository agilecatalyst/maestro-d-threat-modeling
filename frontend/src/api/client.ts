import type {
  JobStatusResponse,
  ThreatModelListItem,
  ThreatModelResult,
} from "../types";

const API_BASE = import.meta.env.VITE_APP_ENDPOINT ?? "";

function jsonHeaders(): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const internalKey = import.meta.env.VITE_INTERNAL_API_KEY;
  if (internalKey) {
    headers["X-Internal-Key"] = internalKey;
  }
  return headers;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export async function uploadDiagram(file: File) {
  const form = new FormData();
  form.append("file", file);
  return request<{ id: string; diagram_path: string; state: string }>(
    "/threat-designer/diagrams/",
    { method: "POST", body: form },
  );
}

export async function startThreatModel(payload: {
  id: string;
  description: string;
  title?: string;
  application_type?: string;
}) {
  return request<{ id: string }>("/threat-designer", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function getJobStatus(id: string) {
  return request<JobStatusResponse>(`/threat-designer/status/${id}`);
}

export async function getThreatModel(id: string) {
  return request<ThreatModelResult>(`/threat-designer/${id}`);
}

export async function listThreatModels(limit = 20) {
  return request<{ items: ThreatModelListItem[]; count: number }>(
    `/threat-designer/all?limit=${limit}`,
  );
}

export async function deleteThreatModel(id: string) {
  return request<{ id: string; deleted: boolean }>(`/threat-designer/${id}`, {
    method: "DELETE",
  });
}

export function diagramFileUrl(id: string): string {
  return `${API_BASE}/threat-designer/diagrams/${id}/file`;
}

export async function getApiHealth(): Promise<{ status: string; database?: string }> {
  const response = await fetch(`${API_BASE}/health`);
  return response.json() as Promise<{ status: string; database?: string }>;
}

export async function retryThreatModel(model: ThreatModelResult) {
  if (!model.input_description?.trim()) {
    throw new Error("No saved description — create a new model from the wizard.");
  }
  return startThreatModel({
    id: model.id,
    description: model.input_description.trim(),
    title: model.title ?? undefined,
    application_type: model.application_type ?? "hybrid",
  });
}

export function mergeStatusIntoModel(
  id: string,
  status: JobStatusResponse,
  prev: ThreatModelResult | null,
): ThreatModelResult {
  const detail = (status.detail ?? {}) as Partial<
    Pick<ThreatModelResult, "summary" | "assets" | "flows" | "threats" | "meta" | "error">
  >;
  return {
    id,
    owner: prev?.owner ?? "local-user",
    title: prev?.title,
    diagram_path: prev?.diagram_path,
    application_type: prev?.application_type,
    input_description: prev?.input_description,
    state: status.state,
    updated_at: status.updated_at ?? prev?.updated_at,
    summary: detail.summary ?? prev?.summary,
    assets: detail.assets ?? prev?.assets,
    flows: detail.flows ?? prev?.flows,
    threats: detail.threats ?? prev?.threats,
    meta: detail.meta ?? prev?.meta,
    error: detail.error ?? prev?.error,
  };
}

/** Default wait for local LLM pipeline (summary → assets → flows → threats loop). */
export const POLL_TIMEOUT_MS = 600_000;

export class PollTimeoutError extends Error {
  readonly lastState: string;

  constructor(lastState: string) {
    super(`Pipeline still running (${lastState}) after ${POLL_TIMEOUT_MS / 60_000} minutes`);
    this.name = "PollTimeoutError";
    this.lastState = lastState;
  }
}

export function pollUntilComplete(
  id: string,
  onTick?: (state: string) => void,
  intervalMs = 2500,
  timeoutMs = POLL_TIMEOUT_MS,
  onStatus?: (status: JobStatusResponse) => void,
): Promise<JobStatusResponse> {
  const started = Date.now();
  let lastState = "PROCESSING";
  return new Promise((resolve, reject) => {
    const tick = async () => {
      try {
        const status = await getJobStatus(id);
        lastState = status.state;
        onTick?.(status.state);
        onStatus?.(status);
        if (status.state === "COMPLETE" || status.state === "FAILED") {
          resolve(status);
          return;
        }
        if (Date.now() - started > timeoutMs) {
          reject(new PollTimeoutError(lastState));
          return;
        }
        window.setTimeout(tick, intervalMs);
      } catch (err) {
        reject(err);
      }
    };
    void tick();
  });
}

export async function downloadExport(id: string, format: "pdf" | "json"): Promise<void> {
  const response = await fetch(`${API_BASE}/threat-designer/${id}/export/${format}`);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Export failed (${response.status})`);
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `threat-model-${id.slice(0, 8)}.${format}`;
  anchor.click();
  URL.revokeObjectURL(url);
}

export type ThreatMutationOp = "add" | "update" | "delete" | "replace";

export async function mutateThreats(
  id: string,
  op: ThreatMutationOp,
  threats: import("../types").Threat[],
) {
  return request<{
    id: string;
    state: string;
    threats: import("../types").Threat[];
    meta: Record<string, unknown>;
  }>(`/threat-designer/${id}/threats`, {
    method: "PATCH",
    headers: jsonHeaders(),
    body: JSON.stringify({ op, threats }),
  });
}

export async function scanFlowThreats(
  id: string,
  flow: { source_entity: string; target_entity: string; flow_description: string },
) {
  return request<{
    id: string;
    added: number;
    threats: import("../types").Threat[];
    meta: Record<string, unknown>;
  }>(`/threat-designer/${id}/threats/scan-flow`, {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify(flow),
  });
}
