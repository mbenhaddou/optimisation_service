"use client";

import { useEffect, useState } from "react";

const defaultApiBase =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

const STORAGE_KEY = "optimise.portal.settings";
const TOKEN_STORAGE_KEY = "optimise.portal.token";

type Profile = {
  id: string;
  email: string;
  role: string;
  org_id?: string | null;
};

type Organization = {
  id: string;
  name: string;
  created_at?: string | null;
};

export default function WorkspacePage() {
  const [apiBase, setApiBase] = useState(defaultApiBase);
  const [token, setToken] = useState("");
  const [profile, setProfile] = useState<Profile | null>(null);
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const stored = JSON.parse(raw);
        if (stored.apiBase) setApiBase(stored.apiBase);
        if (stored.token) setToken(stored.token);
      }
      const fallbackToken = window.localStorage.getItem(TOKEN_STORAGE_KEY);
      if (!token && fallbackToken) setToken(fallbackToken);
    } catch (err) {
      console.warn("Failed to load portal settings", err);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const request = async (path: string) => {
    if (!token.trim()) {
      throw new Error("Log in to load workspace data.");
    }
    const res = await fetch(`${apiBase}${path}`, {
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token.trim()}`,
      },
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const msg = data?.error?.message || data?.detail || "Request failed";
      throw new Error(msg);
    }
    return data;
  };

  const loadWorkspace = async () => {
    setIsLoading(true);
    setError("");
    try {
      const profileData = await request("/v1/portal/me");
      const orgData = await request("/v1/portal/organization");
      setProfile(profileData);
      setOrganization(orgData);
    } catch (err: any) {
      setError(err.message || "Failed to load workspace data.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!token.trim()) return;
    loadWorkspace();
  }, [token]);

  return (
    <div className="portal-page">
      <div className="portal-header">
        <div>
          <h1>Workspace</h1>
          <p className="portal-subtitle">
            Manage your organization profile and workspace context.
          </p>
        </div>
        <div className="portal-header-actions">
          <button className="button secondary" onClick={loadWorkspace} disabled={isLoading}>
            {isLoading ? "Refreshing..." : "Refresh"}
          </button>
          <a className="button primary" href="/portal/settings">
            Manage Settings
          </a>
        </div>
      </div>

      {!token.trim() && (
        <div className="notice-box">
          You are not logged in yet.{" "}
          <a className="button ghost" href="/portal/login">
            Log in
          </a>
        </div>
      )}

      <div className="portal-grid-wide">
        <section className="portal-panel">
          <h3>Organization</h3>
          {organization ? (
            <div className="portal-kv-list">
              <div className="portal-kv">
                <span>Name</span>
                <strong>{organization.name}</strong>
              </div>
              <div className="portal-kv">
                <span>Org ID</span>
                <strong>{organization.id}</strong>
              </div>
            </div>
          ) : (
            <p className="portal-muted">No organization loaded yet.</p>
          )}
        </section>

        <section className="portal-panel">
          <h3>Your Profile</h3>
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
                <span>User ID</span>
                <strong>{profile.id}</strong>
              </div>
            </div>
          ) : (
            <p className="portal-muted">No profile loaded yet.</p>
          )}
        </section>
      </div>

      {error && <div className="error-box">{error}</div>}
    </div>
  );
}
