import { useEffect, useState, type FormEvent } from "react";
import {
  createLlmProvider,
  deleteLlmProvider,
  getLlmRoleBindings,
  listLlmProviders,
  setLlmRoleBinding,
  testLlmProvider,
  updateLlmProvider,
} from "../api/client";
import type {
  LlmProviderKind,
  LlmProviderProfile,
  LlmProviderProfileInput,
  LlmProviderRole,
  LlmProviderTestResult,
  LlmRoleBindings,
} from "../types";

const KINDS: { value: LlmProviderKind; label: string }[] = [
  { value: "openai_compatible", label: "OpenAI-compatible (LM Studio, oMLX, Ollama, vLLM)" },
  { value: "openai", label: "OpenAI cloud" },
  { value: "anthropic", label: "Anthropic (Claude)" },
  { value: "gemini", label: "Google Gemini" },
];

const ROLES: { value: LlmProviderRole; label: string; hint: string }[] = [
  { value: "threats", label: "Threat pipeline", hint: "Summary, assets, flows and STRIDE loop" },
  { value: "sentry", label: "Sentry chat", hint: "The in-app assistant" },
];

const EMPTY_FORM: LlmProviderProfileInput = {
  name: "",
  kind: "openai_compatible",
  base_url: "http://host.docker.internal:1234/v1",
  model: "",
  api_key_env: "INFERENCE_API_KEY",
  temperature: null,
  max_tokens: null,
  timeout_sec: 180,
};

function toForm(profile: LlmProviderProfile): LlmProviderProfileInput {
  return {
    name: profile.name,
    kind: profile.kind,
    base_url: profile.base_url ?? null,
    model: profile.model,
    api_key_env: profile.api_key_env ?? null,
    temperature: profile.temperature ?? null,
    max_tokens: profile.max_tokens ?? null,
    timeout_sec: profile.timeout_sec,
  };
}

export function SettingsPage() {
  const [profiles, setProfiles] = useState<LlmProviderProfile[]>([]);
  const [roles, setRoles] = useState<LlmRoleBindings | null>(null);
  const [form, setForm] = useState<LlmProviderProfileInput>(EMPTY_FORM);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [testingId, setTestingId] = useState<string | null>(null);
  const [results, setResults] = useState<Record<string, LlmProviderTestResult>>({});

  const refresh = () => {
    setLoading(true);
    Promise.all([listLlmProviders(), getLlmRoleBindings()])
      .then(([items, bindings]) => {
        setProfiles(items);
        setRoles(bindings);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    refresh();
  }, []);

  const resetForm = () => {
    setForm(EMPTY_FORM);
    setEditingId(null);
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setError(null);
    const payload: LlmProviderProfileInput = {
      ...form,
      base_url: form.kind === "openai_compatible" ? form.base_url : (form.base_url || null),
      api_key_env: form.api_key_env || null,
    };
    try {
      if (editingId) {
        await updateLlmProvider(editingId, payload);
      } else {
        await createLlmProvider(payload);
      }
      resetForm();
      refresh();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (profile: LlmProviderProfile) => {
    if (!window.confirm(`Delete provider profile "${profile.name}"?`)) return;
    setError(null);
    try {
      await deleteLlmProvider(profile.id);
      if (editingId === profile.id) resetForm();
      refresh();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const handleTest = async (profile: LlmProviderProfile) => {
    setTestingId(profile.id);
    try {
      const result = await testLlmProvider(profile.id);
      setResults((prev) => ({ ...prev, [profile.id]: result }));
    } catch (err) {
      setResults((prev) => ({
        ...prev,
        [profile.id]: { ok: false, latency_ms: 0, error: (err as Error).message },
      }));
    } finally {
      setTestingId(null);
    }
  };

  const handleRoleChange = async (role: LlmProviderRole, profileId: string) => {
    if (!profileId) return;
    setError(null);
    try {
      await setLlmRoleBinding(role, profileId);
      refresh();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <main>
      <section className="panel">
        <h2>Inference providers</h2>
        <p>
          Point Maestro&apos;D at a local OpenAI-compatible server or a cloud API. API keys are
          never stored here — a profile only references the name of an environment variable
          (<code>INFERENCE_API_KEY</code> or <code>LLM_*</code>) read from your <code>.env</code>.
        </p>
        {error && <div className="error-banner">{error}</div>}
      </section>

      <section className="panel">
        <h3>Role assignment</h3>
        {ROLES.map((role) => (
          <div className="field" key={role.value}>
            <label htmlFor={`role-${role.value}`}>
              {role.label} <span style={{ color: "var(--text-muted)" }}>· {role.hint}</span>
            </label>
            <select
              id={`role-${role.value}`}
              value={roles?.[role.value]?.id ?? ""}
              onChange={(event) => handleRoleChange(role.value, event.target.value)}
            >
              <option value="">Environment defaults (INFERENCE_BASE_URL / LOCAL_MODEL)</option>
              {profiles.map((profile) => (
                <option key={profile.id} value={profile.id}>
                  {profile.name} — {profile.model}
                </option>
              ))}
            </select>
          </div>
        ))}
      </section>

      <section className="panel">
        <h3>{editingId ? "Edit profile" : "New profile"}</h3>
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="provider-name">Name</label>
            <input
              id="provider-name"
              value={form.name}
              required
              onChange={(event) => setForm({ ...form, name: event.target.value })}
            />
          </div>
          <div className="field">
            <label htmlFor="provider-kind">Provider</label>
            <select
              id="provider-kind"
              value={form.kind}
              onChange={(event) =>
                setForm({ ...form, kind: event.target.value as LlmProviderKind })
              }
            >
              {KINDS.map((kind) => (
                <option key={kind.value} value={kind.value}>
                  {kind.label}
                </option>
              ))}
            </select>
          </div>
          {form.kind === "openai_compatible" && (
            <div className="field">
              <label htmlFor="provider-base-url">Base URL</label>
              <input
                id="provider-base-url"
                value={form.base_url ?? ""}
                required
                placeholder="http://host.docker.internal:1234/v1"
                onChange={(event) => setForm({ ...form, base_url: event.target.value })}
              />
            </div>
          )}
          <div className="field">
            <label htmlFor="provider-model">Model</label>
            <input
              id="provider-model"
              value={form.model}
              required
              placeholder="qwen3-8b / gpt-4o-mini / claude-sonnet-4 / gemini-2.5-pro"
              onChange={(event) => setForm({ ...form, model: event.target.value })}
            />
          </div>
          <div className="field">
            <label htmlFor="provider-key-env">API key environment variable</label>
            <input
              id="provider-key-env"
              value={form.api_key_env ?? ""}
              placeholder="LLM_ANTHROPIC_API_KEY"
              onChange={(event) => setForm({ ...form, api_key_env: event.target.value })}
            />
          </div>
          <div className="field">
            <label htmlFor="provider-timeout">Request timeout (seconds)</label>
            <input
              id="provider-timeout"
              type="number"
              min={1}
              value={form.timeout_sec}
              onChange={(event) =>
                setForm({ ...form, timeout_sec: Number(event.target.value) || 180 })
              }
            />
          </div>
          <div className="actions-row">
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? "Saving…" : editingId ? "Save changes" : "Create profile"}
            </button>
            {editingId && (
              <button type="button" className="btn btn-ghost" onClick={resetForm}>
                Cancel
              </button>
            )}
          </div>
        </form>
      </section>

      <section className="panel">
        <h3>Profiles</h3>
        {loading ? (
          <p className="empty">Loading…</p>
        ) : profiles.length === 0 ? (
          <p className="empty">
            No profiles yet — Maestro&apos;D is using the environment configuration.
          </p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Provider</th>
                  <th>Model</th>
                  <th>Key</th>
                  <th>Connection</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {profiles.map((profile) => {
                  const result = results[profile.id];
                  return (
                    <tr key={profile.id}>
                      <td>{profile.name}</td>
                      <td>
                        {profile.kind}
                        {profile.base_url && (
                          <div style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>
                            {profile.base_url}
                          </div>
                        )}
                      </td>
                      <td>{profile.model}</td>
                      <td>
                        {profile.api_key_env ? (
                          <>
                            {profile.api_key_env}{" "}
                            <span className={`state-badge ${profile.key_present ? "complete" : "failed"}`}>
                              {profile.key_present ? "set" : "missing"}
                            </span>
                          </>
                        ) : (
                          "—"
                        )}
                      </td>
                      <td>
                        {testingId === profile.id
                          ? "Testing…"
                          : result
                            ? result.ok
                              ? `OK · ${result.latency_ms} ms — ${result.detail ?? ""}`
                              : `Failed — ${result.error ?? "unknown error"}`
                            : "—"}
                      </td>
                      <td>
                        <div className="actions-row">
                          <button
                            type="button"
                            className="btn btn-ghost"
                            onClick={() => handleTest(profile)}
                            disabled={testingId === profile.id}
                          >
                            Test
                          </button>
                          <button
                            type="button"
                            className="btn btn-ghost"
                            onClick={() => {
                              setForm(toForm(profile));
                              setEditingId(profile.id);
                            }}
                          >
                            Edit
                          </button>
                          <button
                            type="button"
                            className="btn btn-ghost"
                            onClick={() => handleDelete(profile)}
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  );
}
