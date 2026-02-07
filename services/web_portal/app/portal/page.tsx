export default function PortalDashboard() {
  return (
    <div className="portal-page">
      <div className="portal-header">
        <div>
          <h1>Dashboard</h1>
          <p className="portal-subtitle">
            Operational overview for your route optimization workspace.
          </p>
        </div>
        <div className="portal-header-actions">
          <a className="button secondary" href="/portal/planner">
            New Optimization
          </a>
          <a className="button primary" href="/portal/api-tools">
            Open API Tools
          </a>
        </div>
      </div>

      <div className="portal-stats">
        <div className="portal-stat-card">
          <span>Active Routes</span>
          <strong>12</strong>
          <p>Running across today's fleet</p>
        </div>
        <div className="portal-stat-card">
          <span>Tasks Scheduled</span>
          <strong>247</strong>
          <p>Across current optimization window</p>
        </div>
        <div className="portal-stat-card">
          <span>API Requests (24h)</span>
          <strong>1,234</strong>
          <p>Stable response times</p>
        </div>
        <div className="portal-stat-card">
          <span>Cost (MTD)</span>
          <strong>$234.50</strong>
          <p>Down 8% from last month</p>
        </div>
      </div>

      <div className="portal-grid-wide">
        <section className="portal-panel">
          <h3>Live Map</h3>
          <div className="portal-map-placeholder">
            Map visualization will appear here once live routes are active.
          </div>
        </section>
        <section className="portal-panel">
          <h3>Recent Activity</h3>
          <ul className="portal-list">
            <li>Optimization job #124 completed in 5.2s</li>
            <li>Route plan SF-North updated by Sarah Johnson</li>
            <li>API key "Prod-West" rotated 2 hours ago</li>
          </ul>
        </section>
      </div>
    </div>
  );
}
