"use client";

import { useEffect, useState } from "react";

const defaultApiBase =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

const SETTINGS_KEY = "optimise.portal.settings";
const TOKEN_STORAGE_KEY = "optimise.portal.token";

export default function AnalyticsPage() {
  const [apiBase, setApiBase] = useState(defaultApiBase);
  const [token, setToken] = useState("");
  const [data, setData] = useState<any>(null);
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

  const loadAnalytics = async () => {
    setError("");
    try {
      const res = await fetch(`${apiBase}/v1/analytics/routes`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(payload?.detail || "Failed to load analytics.");
      }
      setData(payload);
    } catch (err: any) {
      setError(err.message || "Failed to load analytics.");
    }
  };

  useEffect(() => {
    if (!token) return;
    loadAnalytics();
  }, [token]);

  return (
    <div className="portal-page">
      <div className="portal-header">
        <div>
          <h1>Analytics</h1>
          <p className="portal-subtitle">
            Trends, KPIs, and recommendations from recent optimizations.
          </p>
        </div>
        <div className="portal-header-actions">
          <button className="button secondary" onClick={loadAnalytics}>
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
            placeholder="token..."
          />
        </div>
      </section>

      {error && <div className="error-box">{error}</div>}

      {data && (
        <div className="portal-grid-wide">
          <section className="portal-panel">
            <h3>Key Metrics</h3>
            <div className="planner-metrics">
              <div>Total Jobs: {data.total_jobs}</div>
              <div>Completed: {data.completed_jobs}</div>
              <div>Failed: {data.failed_jobs}</div>
              <div>Infeasible Rate: {data.infeasible_rate}</div>
              <div>Average Nodes: {data.average_nodes}</div>
              <div>Average Usage Units: {data.average_usage_units}</div>
              <div>Forecast (7d): {data.demand_forecast_next_7d}</div>
              <div>Capacity Note: {data.capacity_recommendation}</div>
            </div>
          </section>
          <section className="portal-panel">
            <h3>Trends</h3>
            <div className="planner-routes">
              {data.trends?.length ? (
                data.trends.map((point: any) => (
                  <div key={point.date} className="planner-route">
                    <strong>{point.date}</strong>
                    <div>{point.value} jobs</div>
                  </div>
                ))
              ) : (
                <div className="portal-placeholder">No trend data yet.</div>
              )}
            </div>
          </section>
          <section className="portal-panel">
            <h3>Recommendations</h3>
            {data.recommendations?.length ? (
              <ul className="planner-unassigned">
                {data.recommendations.map((rec: any, idx: number) => (
                  <li key={idx}>{rec.message}</li>
                ))}
              </ul>
            ) : (
              <div className="portal-placeholder">No recommendations.</div>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
