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

export default function PortalPage() {
  const [apiBase, setApiBase] = useState(defaultApiBase);
  const [token, setToken] = useState("");
  const [profile, setProfile] = useState<Profile | null>(null);
  const [summary, setSummary] = useState<BillingSummary | null>(null);
  const [checkoutStatus, setCheckoutStatus] = useState<string | null>(null);
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
      const params = new URLSearchParams(window.location.search);
      const checkout = params.get("checkout");
      if (checkout) setCheckoutStatus(checkout);
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
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`${res.status} ${res.statusText}: ${text}`);
    }
    return res.json();
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
      setMessage("Portal data refreshed.");
    } catch (err: any) {
      setError(err.message || "Failed to load portal data.");
    } finally {
      setIsLoading(false);
    }
  };

  const startCheckout = async () => {
    setIsLoading(true);
    setError("");
    try {
      const payload = await request("/v1/billing/checkout", { method: "POST" });
      if (payload?.url) {
        window.location.assign(payload.url);
      } else {
        throw new Error("Checkout URL missing from response.");
      }
    } catch (err: any) {
      setError(err.message || "Failed to create checkout session.");
    } finally {
      setIsLoading(false);
    }
  };

  const openBillingPortal = async () => {
    setIsLoading(true);
    setError("");
    try {
      const payload = await request("/v1/billing/portal", { method: "POST" });
      if (payload?.url) {
        window.location.assign(payload.url);
      } else {
        throw new Error("Billing portal URL missing from response.");
      }
    } catch (err: any) {
      setError(err.message || "Failed to open billing portal.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="page-card">
      <h1>Developer Portal</h1>
      <p>
        Connect your bearer token and review organization profile, usage, and
        billing. Use the console to test the API, then return here to manage
        your plan.
      </p>

      <div className="portal-grid">
        <div className="portal-card">
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
            <button
              className="button primary"
              onClick={refresh}
              disabled={isLoading}
            >
              {isLoading ? "Refreshing..." : "Load Portal Data"}
            </button>
          </div>
          <div className="portal-actions">
            <a className="button secondary" href="/portal/test">
              Open API Test Console
            </a>
          </div>
        </div>

        <div className="portal-card">
          <h3>Organization</h3>
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
              <div className="portal-kv">
                <span>User ID</span>
                <strong>{profile.id}</strong>
              </div>
            </div>
          ) : (
            <p className="portal-muted">No profile loaded yet.</p>
          )}
        </div>

        <div className="portal-card">
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
                <span>Used Units</span>
                <strong>{summary.used_units.toLocaleString()}</strong>
              </div>
              <div className="portal-kv">
                <span>Free Tier Units</span>
                <strong>{summary.free_tier_units.toLocaleString()}</strong>
              </div>
              <div className="portal-kv">
                <span>Overage</span>
                <strong>{summary.overage_units.toLocaleString()}</strong>
              </div>
            </div>
          ) : (
            <p className="portal-muted">No billing data loaded yet.</p>
          )}
          <div className="portal-actions">
            <button className="button primary" onClick={startCheckout} disabled={isLoading}>
              Start Checkout
            </button>
            <button
              className="button secondary"
              onClick={openBillingPortal}
              disabled={isLoading}
            >
              Manage Billing
            </button>
          </div>
          {checkoutStatus && (
            <p className="portal-muted">Checkout status: {checkoutStatus}</p>
          )}
        </div>
      </div>

      {error && <div className="error-box">{error}</div>}
      {message && <div className="notice-box">{message}</div>}
    </div>
  );
}
