"use client";

import { useEffect, useMemo, useState } from "react";

const defaultApiBase =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

const STORAGE_KEYS = {
  form: "optimise.console.form",
  presets: "optimise.console.presets",
  history: "optimise.console.history",
  sharedToken: "optimise.portal.token",
};

const HISTORY_LIMIT = 12;

const samplePayload = {
  language: "en",
  date_format: "%Y-%m-%d %H:%M:%S",
  time_unit: "minutes",
  optimization_target: "duration",
  optimization_horizon: 1,
  period_start: "2024-01-01 08:00:00",
  distance_matrix_method: "haversine",
  driving_speed_kmh: 40,
  deterministic: true,
  random_seed: 42,
  orders: [
    {
      id: "WO-1",
      skill: "electric",
      priority: 3,
      latitude: 50.8503,
      longitude: 4.3517,
      visiting_hour_start: "08:00:00",
      visiting_hour_end: "17:00:00",
      work_hours: 60,
      street: "Rue de la Loi 16",
      postal_code: "1000",
      city: "Brussels",
      country: "BE",
    },
    {
      id: "WO-2",
      skill: "electric",
      priority: 2,
      latitude: 50.8466,
      longitude: 4.3528,
      visiting_hour_start: "08:00:00",
      visiting_hour_end: "17:00:00",
      work_hours: 45,
      street: "Boulevard Anspach 1",
      postal_code: "1000",
      city: "Brussels",
      country: "BE",
    },
  ],
  teams: {
    TeamA: {
      depot: {
        id: "DEPOT-1",
        street: "Rue Ravenstein 2",
        postal_code: "1000",
        city: "Brussels",
        country: "BE",
        latitude: 50.847,
        longitude: 4.355,
      },
      workers: [
        {
          e_id: "W-1",
          skills: ["electric"],
          street: "Rue Royale 10",
          postal_code: "1000",
          city: "Brussels",
          country: "BE",
          latitude: 50.8476,
          longitude: 4.3561,
          day_starts_at: "08:00:00",
          day_ends_at: "17:00:00",
          pause_starts_at: "12:00:00",
          pause_ends_at: "12:30:00",
        },
      ],
    },
  },
  depot: {
    id: "DEPOT-1",
    street: "Rue Ravenstein 2",
    postal_code: "1000",
    city: "Brussels",
    country: "BE",
    latitude: 50.847,
    longitude: 4.355,
  },
};

const samplePayloadText = JSON.stringify(samplePayload, null, 2);

type SavedPreset = {
  id: string;
  name: string;
  method: string;
  path: string;
  body: string;
};

type HistoryEntry = {
  id: string;
  timestamp: string;
  method: string;
  path: string;
  status: number | null;
  latency: number | null;
  body: string;
  error?: string;
};

const builtInPresets: SavedPreset[] = [
  {
    id: "solve",
    name: "Solve (POST)",
    method: "POST",
    path: "/v1/solve",
    body: samplePayloadText,
  },
  {
    id: "jobs",
    name: "Jobs (GET)",
    method: "GET",
    path: "/v1/jobs",
    body: "",
  },
  {
    id: "me",
    name: "Me (GET)",
    method: "GET",
    path: "/v1/portal/me",
    body: "",
  },
  {
    id: "keys",
    name: "API Keys (GET)",
    method: "GET",
    path: "/v1/portal/api-keys",
    body: "",
  },
  {
    id: "keys-create",
    name: "API Keys (POST)",
    method: "POST",
    path: "/v1/portal/api-keys",
    body: JSON.stringify({ name: "default" }, null, 2),
  },
];

export default function ApiTestPage() {
  const [apiBase, setApiBase] = useState(defaultApiBase);
  const [method, setMethod] = useState("POST");
  const [path, setPath] = useState("/v1/solve");
  const [apiKeyHeader, setApiKeyHeader] = useState("X-API-Key");
  const [apiKey, setApiKey] = useState("");
  const [bearer, setBearer] = useState("");
  const [body, setBody] = useState(samplePayloadText);
  const [response, setResponse] = useState("");
  const [status, setStatus] = useState<number | null>(null);
  const [latency, setLatency] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [presetName, setPresetName] = useState("");
  const [savedPresets, setSavedPresets] = useState<SavedPreset[]>([]);
  const [history, setHistory] = useState<HistoryEntry[]>([]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      const storedForm = window.localStorage.getItem(STORAGE_KEYS.form);
      let loadedBearer = "";
      if (storedForm) {
        const parsed = JSON.parse(storedForm);
        if (parsed.apiBase) setApiBase(parsed.apiBase);
        if (parsed.method) setMethod(parsed.method);
        if (parsed.path) setPath(parsed.path);
        if (parsed.apiKeyHeader) setApiKeyHeader(parsed.apiKeyHeader);
        if (parsed.apiKey) setApiKey(parsed.apiKey);
        if (parsed.bearer) loadedBearer = parsed.bearer;
        if (parsed.body) setBody(parsed.body);
      }
      const storedPresets = window.localStorage.getItem(STORAGE_KEYS.presets);
      if (storedPresets) {
        const parsed = JSON.parse(storedPresets);
        if (Array.isArray(parsed)) setSavedPresets(parsed);
      }
      const storedHistory = window.localStorage.getItem(STORAGE_KEYS.history);
      if (storedHistory) {
        const parsed = JSON.parse(storedHistory);
        if (Array.isArray(parsed)) setHistory(parsed);
      }
      const sharedToken = window.localStorage.getItem(STORAGE_KEYS.sharedToken);
      if (!loadedBearer && sharedToken) loadedBearer = sharedToken;
      if (loadedBearer) setBearer(loadedBearer);
    } catch (err) {
      console.warn("Failed to load console state", err);
    }
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const payload = {
      apiBase,
      method,
      path,
      apiKeyHeader,
      apiKey,
      bearer,
      body,
    };
    window.localStorage.setItem(STORAGE_KEYS.form, JSON.stringify(payload));
    window.localStorage.setItem(STORAGE_KEYS.presets, JSON.stringify(savedPresets));
    window.localStorage.setItem(STORAGE_KEYS.history, JSON.stringify(history));
    if (bearer.trim()) {
      window.localStorage.setItem(STORAGE_KEYS.sharedToken, bearer.trim());
    }
  }, [apiBase, method, path, apiKeyHeader, apiKey, bearer, body, savedPresets, history]);

  const requestPreview = useMemo(() => {
    return `${method} ${apiBase}${path}`;
  }, [method, apiBase, path]);

  const applyPreset = (preset: SavedPreset) => {
    setMethod(preset.method);
    setPath(preset.path);
    setBody(preset.body ?? "");
  };

  const savePreset = () => {
    if (!presetName.trim()) {
      setError("Add a name for the preset before saving.");
      return;
    }
    const newPreset: SavedPreset = {
      id: `${Date.now()}`,
      name: presetName.trim(),
      method,
      path,
      body,
    };
    setSavedPresets((prev) => [newPreset, ...prev]);
    setPresetName("");
    setError("");
  };

  const removePreset = (presetId: string) => {
    setSavedPresets((prev) => prev.filter((preset) => preset.id !== presetId));
  };

  const applyHistory = (entry: HistoryEntry) => {
    setMethod(entry.method);
    setPath(entry.path);
    setBody(entry.body ?? "");
  };

  const clearHistory = () => {
    setHistory([]);
  };

  const sendRequest = async () => {
    setIsLoading(true);
    setError("");
    setResponse("");
    setStatus(null);
    setLatency(null);

    let parsedBody: any = undefined;
    if (method !== "GET" && body.trim()) {
      try {
        parsedBody = JSON.parse(body);
      } catch (err: any) {
        setError(`Invalid JSON: ${err.message}`);
        setIsLoading(false);
        return;
      }
    }

    const headers: Record<string, string> = {};
    if (parsedBody) {
      headers["Content-Type"] = "application/json";
    }
    if (apiKey.trim()) {
      headers[apiKeyHeader] = apiKey.trim();
    }
    if (bearer.trim()) {
      headers["Authorization"] = `Bearer ${bearer.trim()}`;
    }

    const start = performance.now();
    let historyStatus: number | null = null;
    let historyLatency: number | null = null;
    let historyError = "";
    try {
      const res = await fetch(`${apiBase}${path}`, {
        method,
        headers,
        body: parsedBody ? JSON.stringify(parsedBody) : undefined,
      });
      const end = performance.now();
      historyLatency = Math.round(end - start);
      setLatency(historyLatency);
      historyStatus = res.status;
      setStatus(res.status);
      const text = await res.text();
      setResponse(text);
    } catch (err: any) {
      const end = performance.now();
      historyLatency = Math.round(end - start);
      setLatency(historyLatency);
      historyError = err.message || "Request failed";
      setError(historyError);
    } finally {
      const entry: HistoryEntry = {
        id: `${Date.now()}`,
        timestamp: new Date().toISOString(),
        method,
        path,
        status: historyStatus,
        latency: historyLatency,
        body,
        error: historyError || undefined,
      };
      setHistory((prev) => [entry, ...prev].slice(0, HISTORY_LIMIT));
      setIsLoading(false);
    }
  };

  return (
    <div className="page-card">
      <h1>API Testing Console</h1>
      <p>
        Use this page to send live requests to the optimisation API. Configure
        API keys or bearer tokens and inspect raw JSON responses.
      </p>

      <div className="test-grid">
        <div className="test-panel">
          <label>API Base</label>
          <input
            value={apiBase}
            onChange={(event) => setApiBase(event.target.value)}
          />

          <label>Method</label>
          <select value={method} onChange={(event) => setMethod(event.target.value)}>
            <option>GET</option>
            <option>POST</option>
            <option>PUT</option>
            <option>DELETE</option>
          </select>

          <label>Path</label>
          <input value={path} onChange={(event) => setPath(event.target.value)} />

          <label>API Key Header</label>
          <input
            value={apiKeyHeader}
            onChange={(event) => setApiKeyHeader(event.target.value)}
          />

          <label>API Key</label>
          <input value={apiKey} onChange={(event) => setApiKey(event.target.value)} />

          <label>Bearer Token</label>
          <input
            value={bearer}
            onChange={(event) => setBearer(event.target.value)}
          />

          <label>JSON Body</label>
          <textarea value={body} onChange={(event) => setBody(event.target.value)} />

          <button className="button primary" onClick={sendRequest} disabled={isLoading}>
            {isLoading ? "Sending..." : "Send Request"}
          </button>
        </div>

        <div className="test-panel">
          <div className="test-presets">
            {builtInPresets.map((preset) => (
              <button
                key={preset.id}
                className="button secondary"
                onClick={() => applyPreset(preset)}
              >
                {preset.name}
              </button>
            ))}
          </div>

          <div className="preset-save">
            <input
              placeholder="Preset name"
              value={presetName}
              onChange={(event) => setPresetName(event.target.value)}
            />
            <button className="button secondary" onClick={savePreset}>
              Save Preset
            </button>
          </div>

          {savedPresets.length > 0 && (
            <div className="preset-list">
              {savedPresets.map((preset) => (
                <div key={preset.id} className="preset-row">
                  <button
                    className="button secondary"
                    onClick={() => applyPreset(preset)}
                  >
                    {preset.name}
                  </button>
                  <button
                    className="button ghost"
                    onClick={() => removePreset(preset.id)}
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          )}

          <div className="request-preview">
            <strong>Request</strong>
            <div>{requestPreview}</div>
          </div>

          <div className="response-meta">
            <div>Status: {status ?? "—"}</div>
            <div>Latency: {latency ? `${latency} ms` : "—"}</div>
          </div>

          {error && <div className="error-box">{error}</div>}

          <label>Response</label>
          <pre className="response-box">{response || "No response yet."}</pre>

          <div className="history-header">
            <strong>Recent Requests</strong>
            <button className="button ghost" onClick={clearHistory}>
              Clear
            </button>
          </div>
          <div className="history-list">
            {history.length === 0 && (
              <div className="history-empty">No history yet.</div>
            )}
            {history.map((entry) => (
              <div key={entry.id} className="history-item">
                <div>
                  <strong>{entry.method}</strong> {entry.path}
                </div>
                <div className="history-meta">
                  <span>{new Date(entry.timestamp).toLocaleString()}</span>
                  <span>{entry.status ?? "—"}</span>
                  <span>{entry.latency ? `${entry.latency} ms` : "—"}</span>
                </div>
                {entry.error && <div className="history-error">{entry.error}</div>}
                <button
                  className="button ghost"
                  onClick={() => applyHistory(entry)}
                >
                  Load
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
