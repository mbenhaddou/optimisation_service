"use client";

import { useEffect, useState } from "react";

const defaultApiBase =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

const STORAGE_KEY = "optimise.portal.settings";
const TOKEN_STORAGE_KEY = "optimise.portal.token";

type BillingSummary = {
  plan_name: string;
  status: string;
  used_units: number;
  free_tier_units: number;
  overage_units: number;
};

type Profile = {
  id: string;
  email: string;
  role: string;
  org_id?: string | null;
  created_at?: string | null;
};

type ApiKey = {
  id: string;
  key: string;
  name?: string | null;
  active: boolean;
  created_at?: string | null;
};

export default function SettingsPage() {
  const [apiBase, setApiBase] = useState(defaultApiBase);
  const [token, setToken] = useState("");
  const [profile, setProfile] = useState<Profile | null>(null);
  const [summary, setSummary] = useState<BillingSummary | null>(null);
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [newKeyName, setNewKeyName] = useState("");
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      let loadedToken = "";
      if (raw) {
        const stored = JSON.parse(raw);
        if (stored.apiBase) setApiBase(stored.apiBase);
        if (stored.token) loadedToken = stored.token;
      }
      const fallbackToken = window.localStorage.getItem(TOKEN_STORAGE_KEY);
      if (!loadedToken && fallbackToken) loadedToken = fallbackToken;
      if (loadedToken) setToken(loadedToken);
    } catch (err) {
      console.warn("Failed to load portal settings", err);
    }
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const payload = JSON.stringify({ apiBase, token });
    window.localStorage.setItem(STORAGE_KEY, payload);
    if (token.trim()) {
      window.localStorage.setItem(TOKEN_STORAGE_KEY, token.trim());
    }
  }, [apiBase, token]);

  const request = async (path: string, options?: RequestInit) => {
    if (!token.trim()) {
      throw new Error("Provide a bearer token first.");
    }
    const res = await fetch(`${apiBase}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token.trim()}`,
        ...(options?.headers ?? {}),
      },
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const msg = data?.error?.message || data?.detail || "Request failed.";
      throw new Error(msg);
    }
    return data;
  };

  const refresh = async () => {
    setIsLoading(true);
    setError("");
    setMessage("");
    try {
      const profilePayload = await request("/v1/portal/me");
      setProfile(profilePayload);
      const billingPayload = await request("/v1/billing/summary");
      setSummary(billingPayload);
      const keyPayload = await request("/v1/portal/api-keys");
      setApiKeys(keyPayload.items ?? []);
      setMessage("Settings refreshed.");
    } catch (err: any) {
      setError(err.message || "Failed to load settings.");
    } finally {
      setIsLoading(false);
    }
  };

  const createKey = async () => {
    setIsLoading(true);
    setError("");
    setMessage("");
    setCreatedKey(null);
    try {
      const payload = await request("/v1/portal/api-keys", {
        method: "POST",
        body: JSON.stringify({ name: newKeyName || "default" }),
      });
      setCreatedKey(payload.key);
      setNewKeyName("");
      await refresh();
    } catch (err: any) {
      setError(err.message || "Failed to create API key.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="portal-page">
      <div className="portal-header">
        <div>
          <h1>Settings</h1>
          <p className="portal-subtitle">
            Manage your profile, billing, and API keys.
          </p>
        </div>
        <div className="portal-header-actions">
          <button className="button secondary" onClick={refresh} disabled={isLoading}>
            {isLoading ? "Refreshing..." : "Refresh"}
          </button>
          <a className="button primary" href="/portal/test">
            API Console
          </a>
        </div>
      </div>

      <div className="portal-grid-wide">
        <section className="portal-panel">
          <h3>Connection</h3>
          <div className="portal-form">
            <label>API Base</label>
            <input
              value={apiBase}
              onChange={(event) => setApiBase(event.target.value)}
            />
            <label>Bearer Token</label>
            <input
              value={token}
              onChange={(event) => setToken(event.target.value)}
              placeholder="Paste a JWT from /v1/auth/login"
            />
          </div>
        </section>

        <section className="portal-panel">
          <h3>Profile</h3>
          {profile ? (
            <div className="portal-kv-list">
              <div className="portal-kv">
                <span>Email</span>
                <strong>{profile.email}</strong>
              </div>
              <div className="portal-kv">
                <span>Role</span>
                <strong>{profile.role}</strong>
              </div>
              <div className="portal-kv">
                <span>Org ID</span>
                <strong>{profile.org_id ?? "-"}</strong>
              </div>
            </div>
          ) : (
            <p className="portal-muted">No profile loaded yet.</p>
          )}
        </section>
      </div>

      <div className="portal-grid-wide">
        <section className="portal-panel">
          <h3>Billing Summary</h3>
          {summary ? (
            <div className="portal-kv-list">
              <div className="portal-kv">
                <span>Plan</span>
                <strong>{summary.plan_name}</strong>
              </div>
              <div className="portal-kv">
                <span>Status</span>
                <strong>{summary.status}</strong>
              </div>
              <div className="portal-kv">
                <span>Usage</span>
                <strong>
                  {summary.used_units} / {summary.free_tier_units}
                </strong>
              </div>
              <div className="portal-kv">
                <span>Overage</span>
                <strong>{summary.overage_units}</strong>
              </div>
            </div>
          ) : (
            <p className="portal-muted">No billing data loaded yet.</p>
          )}
        </section>

        <section className="portal-panel">
          <h3>API Keys</h3>
          <div className="portal-form">
            <label>New Key Name</label>
            <input
              value={newKeyName}
              onChange={(event) => setNewKeyName(event.target.value)}
              placeholder="e.g. Production"
            />
            <button className="button primary" onClick={createKey} disabled={isLoading}>
              {isLoading ? "Creating..." : "Create API Key"}
            </button>
          </div>
          {createdKey && (
            <div className="notice-box">
              New key: <strong>{createdKey}</strong> (copy it now)
            </div>
          )}
          {apiKeys.length ? (
            <div className="portal-kv-list">
              {apiKeys.map((key) => (
                <div key={key.id} className="portal-kv">
                  <span>{key.name || "Unnamed"}</span>
                  <strong>{key.key.slice(0, 6)}***</strong>
                </div>
              ))}
            </div>
          ) : (
            <p className="portal-muted">No API keys loaded yet.</p>
          )}
        </section>
      </div>

      {message && <div className="notice-box">{message}</div>}
      {error && <div className="error-box">{error}</div>}
    </div>
  );
}
