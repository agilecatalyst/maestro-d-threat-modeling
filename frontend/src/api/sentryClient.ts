import { config, isSentryEnabled } from "../config";
import type { ThreatModelResult } from "../types";

function sessionHeader(threatModelId: string) {
  const key = `sentry-seed-${threatModelId}`;
  const seed = sessionStorage.getItem(key) ?? crypto.randomUUID().slice(0, 8);
  sessionStorage.setItem(key, seed);
  return `${threatModelId}/${seed}`;
}

async function sentryRequest<T>(
  threatModelId: string,
  body: Record<string, unknown>,
): Promise<T> {
  const response = await fetch(`${config.sentryBaseUrl}/invocations`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Session-Id": sessionHeader(threatModelId),
    },
    body: JSON.stringify({ input: body }),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Sentry request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export async function sendSentryMessage(
  threatModelId: string,
  message: string,
  model: ThreatModelResult,
): Promise<{ reply: string; tools_used?: string[] }> {
  if (!isSentryEnabled()) {
    throw new Error("Sentry is disabled");
  }

  return sentryRequest(threatModelId, {
    message,
    threat_model_id: threatModelId,
    context: {
      threatModel: {
        title: model.title,
        summary: model.summary,
        assets: model.assets,
        flows: model.flows,
        threats: model.threats,
      },
    },
  });
}

export async function clearSentrySession(threatModelId: string): Promise<void> {
  if (!isSentryEnabled()) return;
  await sentryRequest(threatModelId, { type: "clear", threat_model_id: threatModelId });
}
