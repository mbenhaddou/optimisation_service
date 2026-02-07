"use client";

import { useEffect, useState } from "react";

const defaultApiBase =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

const SETTINGS_KEY = "optimise.portal.settings";
const TOKEN_STORAGE_KEY = "optimise.portal.token";

type User = {
  id: string;
  email: string;
  role: string;
  created_at?: string;
};

const ROLE_OPTIONS = [
  "owner",
  "admin",
  "manager",
  "developer",
  "analyst",
  "viewer",
  "operator",
];

export default function TeamPage() {
  const [apiBase, setApiBase] = useState(defaultApiBase);
  const [token, setToken] = useState("");
  const [items, setItems] = useState<User[]>([]);
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

  const loadUsers = async () => {
    setError("");
    try {
      const res = await fetch(`${apiBase}/v1/portal/users`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(payload?.detail || "Failed to load users.");
      }
      setItems(payload.items || []);
    } catch (err: any) {
      setError(err.message || "Failed to load users.");
    }
  };

  const updateRole = async (userId: string, role: string) => {
    setError("");
    try {
      const res = await fetch(`${apiBase}/v1/portal/users/${userId}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ role }),
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(payload?.detail || "Failed to update role.");
      }
      loadUsers();
    } catch (err: any) {
      setError(err.message || "Failed to update role.");
    }
  };

  useEffect(() => {
    if (!token) return;
    loadUsers();
  }, [token]);

  return (
    <div className="portal-page">
      <div className="portal-header">
        <div>
          <h1>Team</h1>
          <p className="portal-subtitle">Manage team members and roles.</p>
        </div>
        <div className="portal-header-actions">
          <button className="button secondary" onClick={loadUsers}>
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
        </div>
      </section>

      {error && <div className="error-box">{error}</div>}

      <section className="portal-panel">
        <h3>Members</h3>
        <div className="planner-routes">
          {items.length ? (
            items.map((user) => (
              <div key={user.id} className="planner-route">
                <strong>{user.email}</strong>
                <div>Role: {user.role}</div>
                <select
                  value={user.role}
                  onChange={(event) => updateRole(user.id, event.target.value)}
                >
                  {ROLE_OPTIONS.map((role) => (
                    <option key={role} value={role}>
                      {role}
                    </option>
                  ))}
                </select>
              </div>
            ))
          ) : (
            <div className="portal-placeholder">No users found.</div>
          )}
        </div>
      </section>
    </div>
  );
}
