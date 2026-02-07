"use client";

import { useEffect, useState } from "react";

const defaultApiBase =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

const SETTINGS_KEY = "optimise.portal.settings";
const TOKEN_STORAGE_KEY = "optimise.portal.token";

type Report = {
  id: string;
  name: string;
  schedule: string;
  format: string;
  active: boolean;
};

export default function ReportsPage() {
  const [apiBase, setApiBase] = useState(defaultApiBase);
  const [token, setToken] = useState("");
  const [items, setItems] = useState<Report[]>([]);
  const [name, setName] = useState("");
  const [schedule, setSchedule] = useState("0 9 * * 1");
  const [format, setFormat] = useState("csv");
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

  const loadReports = async () => {
    setError("");
    try {
      const res = await fetch(`${apiBase}/v1/reports`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(payload?.detail || "Failed to load reports.");
      }
      setItems(payload.items || []);
    } catch (err: any) {
      setError(err.message || "Failed to load reports.");
    }
  };

  const createReport = async () => {
    setError("");
    try {
      const res = await fetch(`${apiBase}/v1/reports`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ name, schedule, format, active: true }),
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(payload?.detail || "Failed to create report.");
      }
      setName("");
      loadReports();
    } catch (err: any) {
      setError(err.message || "Failed to create report.");
    }
  };

  const deleteReport = async (id: string) => {
    setError("");
    try {
      const res = await fetch(`${apiBase}/v1/reports/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        throw new Error("Failed to delete report.");
      }
      loadReports();
    } catch (err: any) {
      setError(err.message || "Failed to delete report.");
    }
  };

  useEffect(() => {
    if (!token) return;
    loadReports();
  }, [token]);

  return (
    <div className="portal-page">
      <div className="portal-header">
        <div>
          <h1>Reports</h1>
          <p className="portal-subtitle">
            Schedule recurring performance reports for your organization.
          </p>
        </div>
        <div className="portal-header-actions">
          <button className="button secondary" onClick={loadReports}>
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
          <label>Schedule (cron)</label>
          <input
            value={schedule}
            onChange={(event) => setSchedule(event.target.value)}
          />
          <label>Format</label>
          <select value={format} onChange={(event) => setFormat(event.target.value)}>
            <option value="csv">CSV</option>
            <option value="json">JSON</option>
            <option value="geojson">GeoJSON</option>
          </select>
        </div>
        <button className="button primary" onClick={createReport}>
          Create Report
        </button>
      </section>

      {error && <div className="error-box">{error}</div>}

      <section className="portal-panel">
        <h3>Scheduled Reports</h3>
        <div className="planner-routes">
          {items.length ? (
            items.map((report) => (
              <div key={report.id} className="planner-route">
                <strong>{report.name}</strong>
                <div>Schedule: {report.schedule}</div>
                <div>Format: {report.format}</div>
                <button
                  className="button ghost"
                  onClick={() => deleteReport(report.id)}
                >
                  Delete
                </button>
              </div>
            ))
          ) : (
            <div className="portal-placeholder">No reports scheduled.</div>
          )}
        </div>
      </section>
    </div>
  );
}
