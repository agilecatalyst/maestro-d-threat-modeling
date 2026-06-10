export type JobState =
  | "PENDING"
  | "PROCESSING"
  | "SUMMARIZED"
  | "ASSETS_DONE"
  | "FLOWS_DONE"
  | "THREATS_DONE"
  | "COMPLETE"
  | "FAILED";

export interface ThreatModelListItem {
  id: string;
  title?: string | null;
  state: JobState;
  diagram_path?: string | null;
  application_type?: string | null;
  updated_at?: string | null;
}

export interface Asset {
  type: string;
  name: string;
  description: string;
  criticality: string;
}

export interface DataFlow {
  flow_description: string;
  source_entity: string;
  target_entity: string;
}

export interface ThreatSource {
  category: string;
  description: string;
  example: string;
}

export interface Threat {
  name: string;
  stride_category: string;
  description: string;
  target: string;
  source: string;
  likelihood: string;
  impact: string;
  mitigations: string[];
  prerequisites: string[];
  vector: string;
}

export interface ThreatModelResult {
  id: string;
  owner: string;
  title?: string | null;
  diagram_path?: string | null;
  application_type?: string | null;
  state: JobState;
  updated_at?: string | null;
  summary?: string;
  assets?: Asset[];
  flows?: {
    data_flows?: DataFlow[];
    trust_boundaries?: unknown[];
    threat_sources?: ThreatSource[];
  };
  threats?: Threat[];
  meta?: {
    threat_count?: number;
    stride_counts?: Record<string, number>;
  };
  error?: string;
}

export interface JobStatusResponse {
  id: string;
  state: JobState;
  detail?: Record<string, unknown> | null;
  updated_at?: string | null;
  retry?: number;
}
