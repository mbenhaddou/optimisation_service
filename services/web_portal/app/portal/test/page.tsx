"use client";

import { useMemo, useState } from "react";

const defaultApiBase =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

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

const presets = [
  {
    label: "Solve (POST)",
    method: "POST",
    path: "/v1/solve",
    body: samplePayload,
  },
  {
    label: "Jobs (GET)",
    method: "GET",
    path: "/v1/jobs",
  },
  {
    label: "Me (GET)",
    method: "GET",
    path: "/v1/portal/me",
  },
  {
    label: "API Keys (GET)",
    method: "GET",
    path: "/v1/portal/api-keys",
  },
  {
    label: "API Keys (POST)",
    method: "POST",
    path: "/v1/portal/api-keys",
    body: { name: "default" },
  },
];

export default function ApiTestPage() {
  const [apiBase, setApiBase] = useState(defaultApiBase);
  const [method, setMethod] = useState("POST");
  const [path, setPath] = useState("/v1/solve");
  const [apiKeyHeader, setApiKeyHeader] = useState("X-API-Key");
  const [apiKey, setApiKey] = useState("");
  const [bearer, setBearer] = useState("");
  const [body, setBody] = useState(JSON.stringify(samplePayload, null, 2));
  const [response, setResponse] = useState("");
  const [status, setStatus] = useState<number | null>(null);
  const [latency, setLatency] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const requestPreview = useMemo(() => {
    return `${method} ${apiBase}${path}`;
  }, [method, apiBase, path]);

  const applyPreset = (preset: (typeof presets)[number]) => {
    setMethod(preset.method);
    setPath(preset.path);
    if (preset.body) {
      setBody(JSON.stringify(preset.body, null, 2));
    }
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
    try {
      const res = await fetch(`${apiBase}${path}`, {
        method,
        headers,
        body: parsedBody ? JSON.stringify(parsedBody) : undefined,
      });
      const end = performance.now();
      setLatency(Math.round(end - start));
      setStatus(res.status);
      const text = await res.text();
      setResponse(text);
    } catch (err: any) {
      setError(err.message || "Request failed");
    } finally {
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
            {presets.map((preset) => (
              <button
                key={preset.label}
                className="button secondary"
                onClick={() => applyPreset(preset)}
              >
                {preset.label}
              </button>
            ))}
          </div>

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
        </div>
      </div>
    </div>
  );
}
