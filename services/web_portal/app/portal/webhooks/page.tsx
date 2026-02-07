"use client";

import { useEffect, useState } from "react";

const defaultApiBase =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

const SETTINGS_KEY = "optimise.portal.settings";
const TOKEN_STORAGE_KEY = "optimise.portal.token";

type Webhook = {
  id: string;
  name: string;
  url: string;
  events: string[];
  active: boolean;
};

export default function WebhooksPage() {
  const [apiBase, setApiBase] = useState(defaultApiBase);
  const [token, setToken] = useState("");
  const [items, setItems] = useState<Webhook[]>([]);
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [events, setEvents] = useState("optimization.completed");
  const [error, setError] = useState("");

  useEffect(() => {
    if (typeof window === "undefined") return;
    const raw = window.localStorage.getItem(SETTINGS_KEY);
    if (raw) {
      try {
        const parsed = JSON.parse(raw);
        if (parsed.apiBase) setApiBase(parsed.apiBase);
      } catch (err) {
        console.warn("Failed to parse settings", err);
      }
    }
    const storedToken = window.localStorage.getItem(TOKEN_STORAGE_KEY);
    if (storedToken) setToken(storedToken);
  }, []);

  const loadWebhooks = async () => {
    setError("");
    try {
      const res = await fetch(`${apiBase}/v1/webhooks`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(payload?.detail || "Failed to load webhooks.");
      }
      setItems(payload.items || []);
    } catch (err: any) {
      setError(err.message || "Failed to load webhooks.");
    }
  };

  const createWebhook = async () => {
    setError("");
    try {
      const res = await fetch(`${apiBase}/v1/webhooks`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name,
          url,
          events: events
            .split(",")
            .map((e) => e.trim())
            .filter(Boolean),
        }),
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(payload?.detail || "Failed to create webhook.");
      }
      setName("");
      setUrl("");
      setEvents("optimization.completed");
      loadWebhooks();
    } catch (err: any) {
      setError(err.message || "Failed to create webhook.");
    }
  };

  const deleteWebhook = async (id: string) => {
    setError("");
    try {
      const res = await fetch(`${apiBase}/v1/webhooks/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        throw new Error("Failed to delete webhook.");
      }
      loadWebhooks();
    } catch (err: any) {
      setError(err.message || "Failed to delete webhook.");
    }
  };

  useEffect(() => {
    if (!token) return;
    loadWebhooks();
  }, [token]);

  return (
    <div className="portal-page">
      <div className="portal-header">
        <div>
          <h1>Webhooks</h1>
          <p className="portal-subtitle">
            Configure notifications for optimization completion and alerts.
          </p>
        </div>
        <div className="portal-header-actions">
          <button className="button secondary" onClick={loadWebhooks}>
            Refresh
          </button>
        </div>
      </div>

      <section className="portal-panel">
        <div className="form-grid">
          <label>API Base</label>
          <input
            value={apiBase}
            onChange={(event) => setApiBase(event.target.value)}
          />
          <label>Bearer Token</label>
          <input
            value={token}
            onChange={(event) => setToken(event.target.value)}
          />
          <label>Name</label>
          <input value={name} onChange={(event) => setName(event.target.value)} />
          <label>URL</label>
          <input value={url} onChange={(event) => setUrl(event.target.value)} />
          <label>Events (comma)</label>
          <input
            value={events}
            onChange={(event) => setEvents(event.target.value)}
          />
        </div>
        <button className="button primary" onClick={createWebhook}>
          Create Webhook
        </button>
      </section>

      {error && <div className="error-box">{error}</div>}

      <section className="portal-panel">
        <h3>Active Webhooks</h3>
        <div className="planner-routes">
          {items.length ? (
            items.map((hook) => (
              <div key={hook.id} className="planner-route">
                <strong>{hook.name}</strong>
                <div>{hook.url}</div>
                <div>Events: {hook.events.join(", ")}</div>
                <button
                  className="button ghost"
                  onClick={() => deleteWebhook(hook.id)}
                >
                  Delete
                </button>
              </div>
            ))
          ) : (
            <div className="portal-placeholder">No webhooks configured.</div>
          )}
        </div>
      </section>
    </div>
  );
}
